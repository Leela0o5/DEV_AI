import logging
from functools import partial

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from . import config
from .agent import ProjectManagerAgent
from .mcp_client import McpClient
from .tasks import (
    end_of_day_report,
    morning_standup,
    task_monitor,
    test_mcp_connection,
)

logger = logging.getLogger(__name__)


class ProjectScheduler:


    def __init__(self, agent: ProjectManagerAgent, mcp: McpClient):
        self.agent = agent
        self.mcp = mcp
        self.scheduler = BackgroundScheduler(
            timezone=config.TIMEZONE,
            daemon=True,
        )

    def setup_jobs(self) -> None:
        logger.info("Setting up scheduled jobs...")

        self.scheduler.add_job(
            partial(morning_standup, self.agent, self.mcp),
            trigger=CronTrigger(
                hour=config.MORNING_STANDUP_HOUR,
                minute=0,
                timezone=config.TIMEZONE,
            ),
            id="morning_standup",
            name="Morning Standup",
            misfire_grace_time=300, 
        )
        logger.info(
            f"  Morning standup scheduled for {config.MORNING_STANDUP_HOUR}:00"
        )

        # Task monitor (configurable interval, default every 30 min)
        self.scheduler.add_job(
            partial(task_monitor, self.agent, self.mcp),
            trigger=IntervalTrigger(
                minutes=config.TASK_MONITOR_INTERVAL_MINUTES,
            ),
            id="task_monitor",
            name="Task Monitor",
            misfire_grace_time=60,  
        )
        logger.info(
            f"   Task monitor scheduled every {config.TASK_MONITOR_INTERVAL_MINUTES} minutes"
        )

        # End-of-day report (configurable hour, default 5 PM)
        self.scheduler.add_job(
            partial(end_of_day_report, self.agent, self.mcp),
            trigger=CronTrigger(
                hour=config.END_OF_DAY_REPORT_HOUR,
                minute=0,
                timezone=config.TIMEZONE,
            ),
            id="end_of_day_report",
            name="End of Day Report",
            misfire_grace_time=300,  
        )
        logger.info(
            f"   End-of-day report scheduled for {config.END_OF_DAY_REPORT_HOUR}:00"
        )

        logger.info(" All jobs scheduled successfully")

    def start(self) -> None:
        self.setup_jobs()
        self.scheduler.start()
        logger.info(" Scheduler started and running in background")

    def shutdown(self) -> None:
        logger.info(" Shutting down scheduler...")
        self.scheduler.shutdown(wait=True)
        logger.info(" Scheduler shut down")

    def get_jobs(self) -> list[dict]:
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "trigger": str(job.trigger),
                "next_run_time": job.next_run_time,
            })
        return jobs

    def test_run_job(self, job_id: str) -> None:
        job = self.scheduler.get_job(job_id)
        if not job:
            logger.warning(f"Job {job_id} not found")
            return

        logger.info(f"Manually triggering job: {job.name}")
        job.func()
