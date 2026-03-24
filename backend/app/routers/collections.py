# backend/app/routers/collections.py
import asyncio
import json
import math

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.auth import verify_api_key
from app.database import get_db
from app.models import Job
from app.schemas import CollectionLaunchRequest, JobOut
from app.services.collector import subscribe_sse, unsubscribe_sse
from app.worker import BackgroundWorker

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/collections", tags=["collections"], dependencies=[Depends(verify_api_key)])


@router.post("/launch", response_model=JobOut, status_code=201)
@limiter.limit("5/minute")
async def launch_collection(request: Request, req: CollectionLaunchRequest, db: AsyncSession = Depends(get_db)):
    running = await db.execute(select(Job).where(Job.status == "running"))
    if running.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A collection job is already running")

    job = Job(
        categories=req.categories,
        target_count=req.target_count,
        status="pending",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    BackgroundWorker.start_job(job.id)
    return job


@router.get("", response_model=dict)
async def list_collections(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    total = (await db.execute(select(func.count(Job.id)))).scalar() or 0
    offset = (page - 1) * per_page
    result = await db.execute(
        select(Job).order_by(Job.created_at.desc()).offset(offset).limit(per_page)
    )
    jobs = result.scalars().all()
    return {
        "items": [JobOut.model_validate(j).model_dump() for j in jobs],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total > 0 else 0,
    }


@router.get("/{job_id}", response_model=JobOut)
async def get_collection(job_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Collection job not found")
    return job


@router.get("/{job_id}/stream")
async def stream_collection(job_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Collection job not found")

    queue = subscribe_sse(job_id)

    async def event_generator():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": event.event,
                        "data": json.dumps(event.data),
                    }
                    if event.event == "completed" or (event.event == "error" and event.data.get("fatal")):
                        break
                except asyncio.TimeoutError:
                    yield {"event": "ping", "data": ""}
        finally:
            unsubscribe_sse(job_id, queue)

    return EventSourceResponse(event_generator())


@router.post("/{job_id}/cancel")
async def cancel_collection(job_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Collection job not found")
    if job.status != "running":
        raise HTTPException(status_code=409, detail="Job is not running")

    cancelled = BackgroundWorker.cancel_job(job_id)
    job.status = "cancelled"
    job.completed_at = func.now()
    await db.commit()
    return {"detail": "Job cancelled"}
