"""
Scheduler service for automated Z-Bon email sending.
Uses APScheduler for background job management.
"""
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

from app.services.zbon_service import ZBonService
from app.services.email_service import EmailService
from app.core.config import settings
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service to manage scheduled Z-Bon email sending."""

    _scheduler = None
    _job_id = "daily_zbon_email"

    @classmethod
    def start_scheduler(cls):
        """
        Start the background scheduler for automated tasks.
        Must be called once during application startup.
        """
        if not settings.SCHEDULED_ZBON_ENABLED:
            logger.info("Scheduled Z-Bon sending is disabled.")
            return

        if cls._scheduler is not None and cls._scheduler.running:
            logger.warning("Scheduler is already running.")
            return

        try:
            cls._scheduler = BackgroundScheduler()

            # Parse scheduled time (format: "HH:MM")
            hour, minute = map(int, settings.SCHEDULED_ZBON_TIME.split(":"))

            # Add job to run every day at scheduled time
            cls._scheduler.add_job(
                func=cls._send_daily_zbon,
                trigger=CronTrigger(hour=hour, minute=minute),
                id=cls._job_id,
                name="Daily Z-Bon Email Sending",
                replace_existing=True,
                misfire_grace_time=900,  # 15 minutes grace period
            )

            cls._scheduler.start()
            logger.info(f"Scheduler started. Daily Z-Bon email scheduled for {settings.SCHEDULED_ZBON_TIME}")

        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise

    @classmethod
    def stop_scheduler(cls):
        """Stop the background scheduler."""
        if cls._scheduler and cls._scheduler.running:
            cls._scheduler.shutdown()
            cls._scheduler = None
            logger.info("Scheduler stopped.")

    @classmethod
    def _send_daily_zbon():
        """
        Internal method to generate and send Z-Bon for the previous day.
        This runs as a background job.
        """
        try:
            # Get yesterday's date (since Z-Bon is for day that just ended)
            target_date = (datetime.now() - timedelta(days=1)).date()
            target_date_str = target_date.isoformat()

            logger.info(f"Starting scheduled Z-Bon generation for {target_date_str}")

            # Generate Z-Bon
            zbon_data = ZBonService.generate_zbon(
                target_date=target_date_str,
                include_cash_count=False,
                report_type=settings.SCHEDULED_ZBON_REPORT_TYPE,
            )

            # Send via email
            success = EmailService.send_zbon_email(
                recipient=settings.EMAIL_RECIPIENT_ZBON,
                zbon_content=zbon_data["content"],
                date=target_date_str,
            )

            if success:
                logger.info(f"✓ Z-Bon successfully sent for {target_date_str} to {settings.EMAIL_RECIPIENT_ZBON}")
            else:
                logger.error(f"✗ Failed to send Z-Bon for {target_date_str}")

        except Exception as e:
            logger.error(f"Error in scheduled Z-Bon sending: {e}", exc_info=True)

    @classmethod
    def get_scheduler_status(cls) -> dict:
        """Get current scheduler status and next scheduled run time."""
        if not settings.SCHEDULED_ZBON_ENABLED:
            return {
                "enabled": False,
                "message": "Scheduled Z-Bon sending is disabled in configuration.",
            }

        if cls._scheduler is None or not cls._scheduler.running:
            return {
                "enabled": True,
                "running": False,
                "message": "Scheduler is not currently running.",
            }

        try:
            job = cls._scheduler.get_job(cls._job_id)
            if job:
                next_run = job.next_run_time
                return {
                    "enabled": True,
                    "running": True,
                    "scheduled_time": settings.SCHEDULED_ZBON_TIME,
                    "next_run": next_run.isoformat() if next_run else None,
                    "job_id": cls._job_id,
                }
            else:
                return {
                    "enabled": True,
                    "running": True,
                    "message": "Scheduler is running but job not found.",
                }
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {
                "enabled": True,
                "running": True,
                "error": str(e),
            }
