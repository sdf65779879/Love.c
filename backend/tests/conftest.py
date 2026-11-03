import os
import sys
import tempfile
from pathlib import Path

# Set test-only configuration before importing the application.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.update(
    DATABASE_URL="sqlite://",
    SECRET_KEY="test-only-secret-key-at-least-32-characters",
    ADMIN_USERNAME="admin",
    ADMIN_PASSWORD="test-only-password-2026",
    UPLOAD_DIR=tempfile.mkdtemp(prefix="likegirl-tests-"),
    SEED_DEMO="true",
    SMTP_USERNAME="",
    SMTP_PASSWORD="",
    SMTP_FROM="",
)

import importlib

import pytest
from app import main
from app.database import Base, get_db
from app.security import limiter
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def client(monkeypatch):
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    monkeypatch.setattr(importlib.import_module("app.seed"), "SessionLocal", factory)
    monkeypatch.setattr(main, "engine", engine)
    # Integration tests drive the scheduler with explicit dates and mock SMTP.
    monkeypatch.setattr(importlib.import_module("app.reminders"), "check_reminders", lambda db: None)

    def override_db():
        with factory() as db:
            yield db

    main.app.dependency_overrides[get_db] = override_db
    limiter.buckets.clear()
    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def admin(client):
    result = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "test-only-password-2026"},
    )
    assert result.status_code == 200
    return client
