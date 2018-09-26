from apscheduler.schedulers.asyncio import AsyncIOScheduler

from gateway.jobs import init_jobs


async def setup_scheduler(app):
    scheduler = AsyncIOScheduler()
    init_jobs(scheduler, app)
    scheduler.start(paused=app.config.scheduler_paused)

    yield

    scheduler.shutdown()
