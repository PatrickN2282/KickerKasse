from sqlalchemy import inspect, text
from app.models.auth_rate_limit import AuthRateLimit


def migrate_access(engine):
    with engine.begin() as conn:
        columns = {c["name"] for c in inspect(conn).get_columns("users")}
        if "session_version" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN session_version INTEGER NOT NULL DEFAULT 1"))
        AuthRateLimit.__table__.create(conn, checkfirst=True)
        if conn.dialect.name == "postgresql":
            action = next(c for c in inspect(conn).get_columns("audit_logs") if c["name"] == "action")
            if getattr(action["type"], "length", None) is not None and action["type"].length < 64:
                conn.execute(text("ALTER TABLE audit_logs ALTER COLUMN action TYPE VARCHAR(64)"))
