import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler()


def start_scheduler(pipeline_run_func):
    """
    매일 07:00 파이프라인 자동 실행 스케줄러
    pipeline_run_func: 실행할 async 함수
    """
    _scheduler.add_job(
        pipeline_run_func,
        trigger=CronTrigger(hour=7, minute=0, timezone="Asia/Seoul"),
        id="daily_pipeline",
        name="매일 07:00 KST 파이프라인 자동 실행",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("[Scheduler] 파이프라인 스케줄러 시작 — 매일 07:00 KST 자동 실행")


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown()
        logger.info("[Scheduler] 스케줄러 종료")
