"""Shared pytest fixtures.

Most tests use isolated in-memory SQLite databases. PostgreSQL-specific migration and
concurrency tests use TEST_POSTGRES_URL to create and drop a separate randomly named
database per test. Without that explicit URL, PostgreSQL tests are skipped.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_local()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


import os
import uuid
from sqlalchemy import text
from sqlalchemy.engine import make_url

@pytest.fixture()
def pg_engine():
    url = os.getenv("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("Set TEST_POSTGRES_URL for isolated PostgreSQL integration tests")
    database = "kickerkasse_pytest_" + uuid.uuid4().hex
    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{database}"'))
    engine = create_engine(make_url(url).set(database=database))
    try:
        yield engine
    finally:
        engine.dispose()
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE "{database}" WITH (FORCE)'))
        admin.dispose()

