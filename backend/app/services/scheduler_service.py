"""
Scheduler service for automated Z-Bon email sending.
Uses APScheduler for background job management.
"""
from datetime import datetime, timedelta
import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings, resolve_timezone_name
from app.core.database import SessionLocal
from app.models import Product
from app.services.app_settings_service import AppSettingsService
from app.services.database_backup_service import DatabaseBackupService
from app.services.email_service import EmailService
from app.services.zbon_service import ZBonService

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service to manage scheduled Z-Bon email sending."""

    _scheduler = None
    _zbon_job_id = "daily_zbon_email"
    _stock_job_id = "daily_critical_stock_email"
    _backup_job_id = "daily_database_backup_email"

    @classmethod
    def _get_timezone(cls):
        return ZoneInfo(resolve_timezone_name(settings.APP_TIMEZONE))

    @classmethod
    def _load_scheduler_settings(cls) -> dict:
        db = SessionLocal()
        try:
            return AppSettingsService(db).get_email_settings()
        finally:
            db.close()

    @classmethod
    def start_scheduler(cls):
        config = cls._load_scheduler_settings()
        timezone = cls._get_timezone()
        has_zbon_schedule = bool(config.get("scheduled_zbon_enabled"))
        has_stock_schedule = bool(config.get("email_critical_stock_enabled"))
        has_backup_schedule = bool(config.get("scheduled_database_backup_enabled"))
        if not config.get("email_enabled") or not (has_zbon_schedule or has_stock_schedule or has_backup_schedule):
            logger.info("Scheduled email jobs are disabled.")
            return

        if cls._scheduler is None:
            cls._scheduler = BackgroundScheduler(timezone=timezone)
        elif not cls._scheduler.running and cls._scheduler.state == 0:
            cls._scheduler = BackgroundScheduler(timezone=timezone)

        try:
            if has_zbon_schedule:
                zbon_hour, zbon_minute = map(int, str(config.get("scheduled_zbon_time") or "23:59").split(":"))
                cls._scheduler.add_job(
                    func=cls._send_daily_zbon,
                    trigger=CronTrigger(hour=zbon_hour, minute=zbon_minute, timezone=timezone),
                    id=cls._zbon_job_id,
                    name="Daily Z-Bon Email Sending",
                    replace_existing=True,
                    misfire_grace_time=900,
                )
            else:
                cls._remove_job_if_exists(cls._zbon_job_id)

            if has_stock_schedule:
                stock_hour, stock_minute = map(int, str(config.get("scheduled_stock_warning_time") or "09:00").split(":"))
                cls._scheduler.add_job(
                    func=cls._send_critical_stock,
                    trigger=CronTrigger(hour=stock_hour, minute=stock_minute, timezone=timezone),
                    id=cls._stock_job_id,
                    name="Daily Critical Stock Email",
                    replace_existing=True,
                    misfire_grace_time=900,
                )
            else:
                cls._remove_job_if_exists(cls._stock_job_id)

            if has_backup_schedule:
                backup_hour, backup_minute = map(int, str(config.get("scheduled_database_backup_time") or "03:00").split(":"))
                cls._scheduler.add_job(
                    func=cls._send_database_backup,
                    trigger=CronTrigger(hour=backup_hour, minute=backup_minute, timezone=timezone),
                    id=cls._backup_job_id,
                    name="Daily Database Backup Email Sending",
                    replace_existing=True,
                    misfire_grace_time=900,
                )
            else:
                cls._remove_job_if_exists(cls._backup_job_id)

            if not cls._scheduler.get_jobs():
                logger.info("No scheduled jobs configured after reload.")
                return
            if not cls._scheduler.running:
                cls._scheduler.start()
            logger.info("Scheduler started with configured jobs.")
        except Exception as e:
            logger.error("Failed to start scheduler: %s", e)
            raise

    @classmethod
    def _remove_job_if_exists(cls, job_id: str):
        if cls._scheduler is None:
            return
        try:
            if cls._scheduler.get_job(job_id):
                cls._scheduler.remove_job(job_id)
        except Exception:
            pass

    @classmethod
    def stop_scheduler(cls):
        if cls._scheduler and cls._scheduler.running:
            cls._scheduler.shutdown()
            cls._scheduler = None
            logger.info("Scheduler stopped.")
        elif cls._scheduler is not None:
            cls._scheduler = None

    @classmethod
    def reload_scheduler(cls):
        cls.stop_scheduler()
        cls.start_scheduler()

    @classmethod
    def _send_daily_zbon(cls):
        db = SessionLocal()
        try:
            config = AppSettingsService(db).get_email_settings()
            if not config.get("email_enabled") or not config.get("scheduled_zbon_enabled"):
                logger.info("Skipping scheduled Z-Bon email because the feature is disabled.")
                return

            recipient = (config.get("email_recipient_zbon") or "").strip()
            if not recipient:
                logger.warning("Skipping scheduled Z-Bon email because no recipient is configured.")
                cls._record_delivery(db, "zbon", "FAILED", "Kein Empfänger für den Kassenbericht konfiguriert")
                return

            target_date = (datetime.now(cls._get_timezone()) - timedelta(days=1)).date()
            target_date_str = target_date.isoformat()
            logger.info("Starting scheduled daily update generation for %s", target_date_str)

            zbon_service = ZBonService(db)
            zbon_data = zbon_service.generate_daily_html_update(target_date)

            success = EmailService.send_zbon_html_email(
                recipient=recipient,
                html_zbon=zbon_data["html"],
                date=zbon_data["business_date"],
                seq_number=zbon_data.get("sequence_number"),
                informational_only=True,
            )

            if success:
                logger.info("✓ Z-Bon successfully sent for %s to %s", target_date_str, recipient)
                cls._record_delivery(db, "zbon", "SUCCESS", f"Kassenbericht für {target_date_str} an {recipient} versendet", target_date_str)
            else:
                logger.error("✗ Failed to send Z-Bon for %s", target_date_str)
                cls._record_delivery(db, "zbon", "FAILED", f"Kassenbericht für {target_date_str} konnte nicht versendet werden", target_date_str)
        except Exception as e:
            logger.error("Error in scheduled Z-Bon sending: %s", e, exc_info=True)
            db.rollback()
            cls._record_delivery(db, "zbon", "FAILED", f"Versandfehler: {e}")
        finally:
            db.close()

    @classmethod
    def _record_delivery(cls, db, channel: str, status: str, message: str, business_date: str | None = None):
        settings_row = AppSettingsService(db).get_or_create_settings()
        prefix = "zbon" if channel == "zbon" else "stock"
        setattr(settings_row, f"{prefix}_last_run_at", datetime.now(cls._get_timezone()).replace(tzinfo=None))
        setattr(settings_row, f"{prefix}_last_run_status", status)
        setattr(settings_row, f"{prefix}_last_run_message", str(message)[:2000])
        if prefix == "zbon" and business_date is not None:
            settings_row.zbon_last_business_date = business_date
        db.commit()

    @classmethod
    def _send_critical_stock(cls):
        db = SessionLocal()
        try:
            config = AppSettingsService(db).get_email_settings()
            if not config.get("email_enabled") or not config.get("email_critical_stock_enabled"):
                logger.info("Skipping critical stock email because the feature is disabled.")
                return

            recipient = (config.get("email_recipient_stock") or "").strip() or (
                config.get("email_recipient_zbon") or ""
            ).strip()
            if not recipient:
                cls._record_delivery(db, "stock", "FAILED", "Kein Empfänger für Lagerwarnungen konfiguriert")
                return

            low_stock_products = (
                db.query(Product)
                .filter(Product.is_active.is_(True))
                .filter(Product.is_unlimited_stock.is_(False))
                .filter(Product.notify_on_low_stock.is_(True))
                .filter(Product.stock_quantity < Product.minimum_stock_quantity)
                .order_by(Product.name.asc())
                .all()
            )
            payload = [
                {
                    "name": product.name,
                    "stock_quantity": product.stock_quantity,
                    "minimum_stock_quantity": product.minimum_stock_quantity,
                }
                for product in low_stock_products
            ]
            if not payload:
                cls._record_delivery(db, "stock", "SKIPPED", "Keine kritischen Lagerbestände; keine E-Mail erforderlich")
                return

            if EmailService.send_critical_stock_email(recipient, payload):
                cls._record_delivery(db, "stock", "SUCCESS", f"Lagerwarnung mit {len(payload)} Positionen an {recipient} versendet")
                logger.info("✓ Critical stock email sent with %s entries", len(payload))
            else:
                cls._record_delivery(db, "stock", "FAILED", "Lagerwarnung konnte nicht versendet werden")
                logger.error("✗ Failed to send critical stock email")
        except Exception as e:
            logger.error("Error in critical stock sending: %s", e, exc_info=True)
            db.rollback()
            cls._record_delivery(db, "stock", "FAILED", f"Versandfehler: {e}")
        finally:
            db.close()

    @classmethod
    def _send_database_backup(cls):
        db = SessionLocal()
        try:
            config = AppSettingsService(db).get_email_settings()
            if not config.get("email_enabled") or not config.get("scheduled_database_backup_enabled"):
                logger.info("Skipping scheduled database backup because the feature is disabled.")
                return

            # Use dedicated backup recipient if configured, fall back to Z-Bon recipient.
            backup_recipient = (config.get("email_recipient_backup") or "").strip()
            recipient = backup_recipient or (config.get("email_recipient_zbon") or "").strip()
            if not recipient:
                logger.warning("Skipping scheduled database backup because no recipient is configured.")
                return

            backup_content, backup_filename = DatabaseBackupService(db).create_backup_zip()
            now = datetime.now(cls._get_timezone())
            target_date = now.date().isoformat()
            subject = EmailService.build_operational_subject(
                "DB-Backup", "email_subject_backup_info", config, occurred_at=now,
            )
            body = (
                f"Automatisches Datenbank-Backup vom {target_date}.\n"
                "Die ZIP-Datei ist als Anhang enthalten."
            )
            html_body = (
                f"<p>Automatisches Datenbank-Backup vom <strong>{target_date}</strong>.</p>"
                "<p>Die ZIP-Datei ist als Anhang enthalten.</p>"
            )
            sent = EmailService.send_email(
                to_address=recipient,
                subject=subject,
                body=body,
                html_body=html_body,
                attachments=[(backup_filename, backup_content, "application/zip")],
            )
            if sent:
                logger.info("✓ Database backup successfully sent")
            else:
                logger.error("✗ Failed to send database backup")
        except Exception as e:
            logger.error("Error in scheduled database backup sending: %s", e, exc_info=True)
        finally:
            db.close()

    @classmethod
    def get_scheduler_status(cls) -> dict:
        config = cls._load_scheduler_settings()
        email_enabled = bool(config.get("email_enabled"))
        scheduler_running = bool(cls._scheduler is not None and cls._scheduler.running)

        def channel(job_id: str, enabled: bool, scheduled_time: str) -> dict:
            job = cls._scheduler.get_job(job_id) if scheduler_running else None
            if not enabled:
                message = "Deaktiviert"
            elif not email_enabled:
                message = "E-Mail-Versand ist deaktiviert"
            elif not scheduler_running:
                message = "Scheduler ist nicht aktiv"
            elif job is None:
                message = "Konfigurierter Job wurde nicht gefunden"
            else:
                message = "Aktiv"
            return {
                "enabled": enabled,
                "running": job is not None,
                "scheduled_time": scheduled_time,
                "next_run": job.next_run_time.isoformat() if job and job.next_run_time else None,
                "message": message,
            }

        zbon = channel(
            cls._zbon_job_id,
            bool(config.get("scheduled_zbon_enabled")),
            config.get("scheduled_zbon_time") or "23:59",
        )
        stock = channel(
            cls._stock_job_id,
            bool(config.get("email_critical_stock_enabled")),
            config.get("scheduled_stock_warning_time") or "09:00",
        )
        backup = channel(
            cls._backup_job_id,
            bool(config.get("scheduled_database_backup_enabled")),
            config.get("scheduled_database_backup_time") or "03:00",
        )
        return {
            # Legacy Z-Bon fields remain for existing clients.
            **zbon,
            "email_enabled": email_enabled,
            "zbon": zbon,
            "stock": stock,
            "database_backup": backup,
            "database_backup_enabled": backup["enabled"],
            "database_backup_time": backup["scheduled_time"],
        }
