# backend/app/main.py
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import async_session
from app.models import Job
from app.routers import collections, games, health
from app.worker import BackgroundWorker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Recover interrupted jobs on startup
    try:
        async with async_session() as db:
            result = await db.execute(select(Job).where(Job.status == "running"))
            running_jobs = result.scalars().all()
            for job in running_jobs:
                BackgroundWorker.start_job(job.id)
                print(f"Recovered job {job.id}")
    except Exception as e:
        print(f"Warning: could not recover running jobs on startup: {e}")
    yield


app = FastAPI(title="TousLesJeux API", lifespan=lifespan)
app.state.limiter = collections.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

app.include_router(health.router)
app.include_router(games.router)
app.include_router(collections.router)

# Serve React static build in production (must be AFTER API routers)
if os.path.isdir("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
