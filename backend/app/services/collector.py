# backend/app/services/collector.py
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models import Game, Job
from app.services.dedup import is_duplicate
from app.services.enricher import enrich_game
from app.services.scraper import discover_games

logger = logging.getLogger(__name__)

JOB_TIMEOUT_HOURS = 2


@dataclass
class SSEEvent:
    event: str
    data: dict

    @staticmethod
    def progress(processed: int, total: int, skipped: int, current_game: str) -> "SSEEvent":
        return SSEEvent(event="progress", data={
            "processed": processed, "total": total, "skipped": skipped, "current_game": current_game,
        })

    @staticmethod
    def game_added(game_id: int, title: str) -> "SSEEvent":
        return SSEEvent(event="game_added", data={"id": game_id, "title": title, "status": "enriched"})

    @staticmethod
    def game_skipped(game_id: int, title: str, reason: str) -> "SSEEvent":
        return SSEEvent(event="game_skipped", data={"id": game_id, "title": title, "reason": reason})

    @staticmethod
    def completed(processed: int, skipped: int, failed: int) -> "SSEEvent":
        return SSEEvent(event="completed", data={"processed": processed, "skipped": skipped, "failed": failed})

    @staticmethod
    def error(message: str, fatal: bool = False) -> "SSEEvent":
        return SSEEvent(event="error", data={"message": message, "fatal": fatal})


# Global dict to store SSE queues per job_id
_sse_queues: dict[int, list[asyncio.Queue]] = {}


def subscribe_sse(job_id: int) -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue()
    _sse_queues.setdefault(job_id, []).append(queue)
    return queue


def unsubscribe_sse(job_id: int, queue: asyncio.Queue) -> None:
    queues = _sse_queues.get(job_id, [])
    if queue in queues:
        queues.remove(queue)


def _publish_sse(job_id: int, event: SSEEvent) -> None:
    for queue in _sse_queues.get(job_id, []):
        queue.put_nowait(event)


async def run_collection(job_id: int) -> None:
    async with async_session() as db:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            logger.error("Job %d not found", job_id)
            return

        job.status = "running"
        await db.commit()

        start_time = datetime.now()
        consecutive_failures = 0

        try:
            scraped_games = await discover_games(job.categories)
            logger.info("Job %d: discovered %d potential games", job_id, len(scraped_games))

            for scraped in scraped_games:
                if datetime.now() - start_time > timedelta(hours=JOB_TIMEOUT_HOURS):
                    job.status = "failed"
                    job.error_message = "timeout"
                    job.completed_at = datetime.now()
                    await db.commit()
                    _publish_sse(job_id, SSEEvent.error("Job timeout after 2 hours", fatal=True))
                    return

                if job.processed_count >= job.target_count:
                    break

                if await is_duplicate(db, scraped.title, scraped.year):
                    continue

                _publish_sse(job_id, SSEEvent.progress(
                    job.processed_count, job.target_count, job.skipped_count, scraped.title,
                ))

                try:
                    enrichment = await enrich_game(scraped.title, scraped.year, scraped.raw_text)
                except RuntimeError as e:
                    job.status = "failed"
                    job.error_message = str(e)
                    job.completed_at = datetime.now()
                    await db.commit()
                    _publish_sse(job_id, SSEEvent.error(str(e), fatal=True))
                    return

                if enrichment is None:
                    game = Game(
                        title=scraped.title,
                        year=scraped.year,
                        source_url=scraped.source_url,
                        status="failed",
                        job_id=job_id,
                        scraped_at=scraped.scraped_at,
                    )
                    db.add(game)
                    await db.flush()
                    job.failed_count += 1
                    await db.commit()
                    consecutive_failures += 1
                    _publish_sse(job_id, SSEEvent.game_skipped(game.id, scraped.title, "enrichment_failed"))

                    if consecutive_failures >= 3:
                        logger.warning("3 consecutive failures, pausing 60s")
                        await asyncio.sleep(60)
                        consecutive_failures = 0
                    continue

                word_count = len(enrichment.regles_detaillees.split())
                status = "enriched"
                skip_reason = None
                if word_count > 1800:
                    status = "skipped"
                    skip_reason = "rules_too_long"

                game = Game(
                    **enrichment.model_dump(exclude={"title"}),
                    title=enrichment.title or scraped.title,
                    source_url=scraped.source_url,
                    status=status,
                    skip_reason=skip_reason,
                    job_id=job_id,
                    scraped_at=scraped.scraped_at,
                    enriched_at=datetime.now(),
                )
                db.add(game)
                await db.flush()

                if status == "enriched":
                    job.processed_count += 1
                    consecutive_failures = 0
                    _publish_sse(job_id, SSEEvent.game_added(game.id, game.title))
                else:
                    job.skipped_count += 1
                    _publish_sse(job_id, SSEEvent.game_skipped(game.id, game.title, skip_reason))

                await db.commit()

            job.status = "completed"
            job.completed_at = datetime.now()
            await db.commit()
            _publish_sse(job_id, SSEEvent.completed(job.processed_count, job.skipped_count, job.failed_count))

        except asyncio.CancelledError:
            logger.info("Job %d cancelled", job_id)
            job.status = "cancelled"
            job.completed_at = datetime.now()
            await db.commit()
            _publish_sse(job_id, SSEEvent.completed(job.processed_count, job.skipped_count, job.failed_count))
            raise
        except Exception as e:
            logger.exception("Job %d failed: %s", job_id, e)
            job.status = "failed"
            job.error_message = str(e)[:500]
            job.completed_at = datetime.now()
            await db.commit()
            _publish_sse(job_id, SSEEvent.error(str(e)[:200], fatal=True))
