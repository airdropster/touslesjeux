# backend/app/worker.py
import asyncio
import logging
from typing import ClassVar

logger = logging.getLogger(__name__)


class BackgroundWorker:
    _tasks: ClassVar[dict[int, asyncio.Task]] = {}

    @classmethod
    def start_job(cls, job_id: int) -> None:
        from app.services.collector import run_collection

        if job_id in cls._tasks and not cls._tasks[job_id].done():
            logger.warning("Job %d is already running", job_id)
            return

        task = asyncio.create_task(run_collection(job_id))
        cls._tasks[job_id] = task
        task.add_done_callback(lambda t: cls._cleanup(job_id, t))

    @classmethod
    def _cleanup(cls, job_id: int, task: asyncio.Task) -> None:
        cls._tasks.pop(job_id, None)
        if not task.cancelled() and task.exception():
            logger.error("Job %d crashed: %s", job_id, task.exception())

    @classmethod
    def cancel_job(cls, job_id: int) -> bool:
        task = cls._tasks.get(job_id)
        if task and not task.done():
            task.cancel()
            return True
        return False

    @classmethod
    def is_running(cls, job_id: int) -> bool:
        task = cls._tasks.get(job_id)
        return task is not None and not task.done()
