from datetime import datetime

from app import mail
from app.database import get_db
from app.main import app
from app.reminders import SHANGHAI, check_reminders


def configure(admin, same=False):
    admin.patch(
        "/api/admin/site",
        json={
            "boy_qq": "12345678",
            "girl_qq": "12345678" if same else "87654321",
            "boy_name": "小明",
            "girl_name": "小花",
        },
    ).raise_for_status()
    admin.put(
        "/api/admin/mail",
        json={
            "enabled": True,
            "host": "smtp.qq.com",
            "port": 465,
            "security": "ssl",
            "username": "12345678@qq.com",
            "password": "test-smtp-only",
        },
    ).raise_for_status()


def scan(iso):
    # A new DB session for each tick, just like a scheduler or process restart.
    sessions = app.dependency_overrides[get_db]()
    try:
        check_reminders(
            next(sessions), datetime.fromisoformat(iso).astimezone(SHANGHAI)
        )
    finally:
        sessions.close()


def test_annual_leap_day_deliveries_and_restart(admin, monkeypatch):
    configure(admin)
    admin.post(
        "/api/admin/anniversaries",
        json={"title": "相遇 <3", "date": "2024-02-29", "annual": True},
    ).raise_for_status()
    admin.post(
        "/api/admin/anniversaries",
        json={"title": "过去的日子", "date": "2024-02-29", "annual": False},
    ).raise_for_status()
    sent = []
    monkeypatch.setattr(
        mail,
        "smtp_send",
        lambda config, recipient, subject, body: sent.append((recipient, body)),
    )
    scan("2025-02-25T10:00:00+08:00")
    scan("2025-02-26T00:59:00+00:00")
    assert not sent
    scan("2025-02-26T01:00:00+00:00")
    scan("2025-02-26T18:00:00+08:00")
    assert [r for r, _ in sent] == ["12345678@qq.com", "87654321@qq.com"]
    assert "亲爱的小明" in sent[0][1].text and "亲爱的小花" in sent[1][1].text
    assert "相遇 &lt;3" in sent[0][1].html and "2025 年 02 月 28 日" in sent[0][1].text
    scan("2026-02-26T19:00:00+08:00")
    assert len(sent) == 4


def test_once_only_and_retries(admin, monkeypatch):
    configure(admin, same=True)
    admin.post(
        "/api/admin/anniversaries",
        json={"title": "明年的旅行", "date": "2027-01-01", "annual": False},
    ).raise_for_status()
    attempts = []

    def sender(*args):
        attempts.append(1)
        if len(attempts) == 1:
            raise mail.MailError("连接失败")
        if len(attempts) == 2:
            raise mail.MailUncertain("提交结果待确认")

    monkeypatch.setattr(mail, "smtp_send", sender)
    for hour in (10, 10, 11, 12):
        scan(f"2026-12-30T{hour}:00:00+08:00")
    scan("2027-12-30T10:00:00+08:00")
    assert len(attempts) == 2
    logs = admin.get("/api/admin/mail/deliveries").json()
    reminders = [r for r in logs if r["event"] == "ANNIVERSARY_REMINDER"]
    assert len(reminders) == 1 and reminders[0]["status"] == "uncertain"
