"""Schema additions for independently scheduled mail jobs and persistent outcomes."""
from sqlalchemy import inspect, text


def migrate_mail_status(engine) -> None:
    if "app_settings" not in inspect(engine).get_table_names():
        return

    columns = {column["name"] for column in inspect(engine).get_columns("app_settings")}
    additions = {
        "scheduled_stock_warning_time": "VARCHAR(5) DEFAULT '09:00' NOT NULL",
        "zbon_last_run_at": "TIMESTAMP",
        "zbon_last_run_status": "VARCHAR(16)",
        "zbon_last_run_message": "TEXT",
        "zbon_last_business_date": "VARCHAR(10)",
        "stock_last_run_at": "TIMESTAMP",
        "stock_last_run_status": "VARCHAR(16)",
        "stock_last_run_message": "TEXT",
    }
    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE app_settings ADD COLUMN {name} {definition}"))
