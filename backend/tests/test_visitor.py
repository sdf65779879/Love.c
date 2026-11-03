from datetime import timedelta
from io import BytesIO

import pytest
from app import mail
from app.database import get_db
from app.main import app
from app.models import EmailChallenge, VisitorSession, utcnow
from app.visitor import COOKIE
from PIL import Image


@pytest.fixture
def private_client(admin, monkeypatch):
    assert (
        admin.patch(
            "/api/admin/site", json={"boy_qq": "12345678", "girl_qq": "87654321"}
        ).status_code
        == 200
    )
    sent = []
    monkeypatch.setattr(
        mail, "send_login_code", lambda email, code, db: sent.append((email, code))
    )
    admin.cookies.clear()
    return admin, sent


def send(client, email="12345678@qq.com"):
    return client.post("/api/visitor/code", json={"email": email})


def login(client, sent):
    email, code = sent[-1]
    return client.post("/api/visitor/login", json={"email": email, "code": code})


def db_session():
    return next(app.dependency_overrides[get_db]())


@pytest.mark.parametrize(
    "path",
    [
        "/api/site",
        "/api/content/articles",
        "/api/content/photos",
        "/api/content/wishes",
        "/api/content/gifts",
        "/api/content/messages",
        "/api/articles/1",
        "/uploads/" + "a" * 32 + ".webp",
        "/api/visitor/me",
        "/api/visitor/access",
    ],
)
def test_anonymous_cannot_read_private_content(client, path):
    result = client.get(path)
    assert result.status_code == 401
    assert result.headers["cache-control"] == "no-store"


def test_anonymous_cannot_write_message(client):
    assert (
        client.post(
            "/api/messages", json={"name": "test", "content": "test"}
        ).status_code
        == 401
    )


@pytest.mark.parametrize(
    "email", ["12345678@qq.com", "87654321@qq.com", " 12345678@QQ.COM "]
)
def test_private_login_both_partners(private_client, email):
    client, sent = private_client
    assert send(client, email).status_code == 200
    assert len(sent) == 1 and len(sent[0][1]) == 6
    response = login(client, sent)
    assert response.status_code == 200
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=strict" in response.headers["set-cookie"]
    assert client.get("/api/site").status_code == 200
    assert client.get("/api/content/photos").status_code == 200
    assert client.get("/api/visitor/me").json() == {"authenticated": True}
    assert client.get("/api/admin/content/photos").status_code == 401
    assert (
        client.patch("/api/admin/site", json={"title": "intruder"}).status_code == 401
    )
    assert login(client, sent).status_code == 400  # Single use.
    token = client.cookies.get(COOKIE)
    assert client.post("/api/visitor/logout").status_code == 200
    client.cookies.set(COOKIE, token)
    assert client.get("/api/site").status_code == 401  # Server revocation.


def test_no_outsider_mail_or_recipient_disclosure(private_client):
    client, sent = private_client
    response = send(client, "11223344@qq.com")
    assert response.status_code == 200 and sent == []
    assert "12345678" not in response.text and "87654321" not in response.text
    assert (
        client.post(
            "/api/visitor/login", json={"email": "11223344@qq.com", "code": "123456"}
        ).status_code
        == 400
    )
    for email in [
        "12345678@example.com",
        "0@qq.com",
        "a@qq.com",
        "12345678@qq.com\r\nBcc:a@b.com",
    ]:
        assert send(client, email).status_code == 422


def test_expiry_attempts_and_hash_storage(private_client):
    client, sent = private_client
    assert send(client).status_code == 200
    with db_session() as db:
        challenge = db.get(EmailChallenge, "12345678")
        assert challenge.digest != sent[-1][1] and len(challenge.digest) == 64
    wrong = "000000" if sent[-1][1] != "000000" else "111111"
    for _ in range(5):
        assert (
            client.post(
                "/api/visitor/login", json={"email": sent[-1][0], "code": wrong}
            ).status_code
            == 400
        )
    assert login(client, sent).status_code == 400
    with db_session() as db:
        challenge = db.get(EmailChallenge, "12345678")
        challenge.attempts = 0
        challenge.expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    assert login(client, sent).status_code == 400


def test_resend_cooldown_hourly_budget_and_old_code(private_client):
    client, sent = private_client
    assert send(client).status_code == 200
    old = sent[-1]
    assert send(client).status_code == 429
    with db_session() as db:
        db.get(EmailChallenge, "12345678").sent_at -= timedelta(seconds=61)
        db.commit()
    assert send(client).status_code == 200
    if old[1] != sent[-1][1]:
        assert (
            client.post(
                "/api/visitor/login", json={"email": old[0], "code": old[1]}
            ).status_code
            == 400
        )
    with db_session() as db:
        challenge = db.get(EmailChallenge, "12345678")
        challenge.sent_at -= timedelta(seconds=61)
        challenge.send_count = 5
        db.commit()
    assert send(client).status_code == 429


def test_mail_failure_no_code_or_secret_leak(private_client, monkeypatch):
    client, sent = private_client

    def fail(*args):
        raise RuntimeError("secret-auth-code-must-not-leak")

    monkeypatch.setattr(mail, "send_login_code", fail)
    response = send(client)
    assert response.status_code == 503
    assert "secret-auth" not in response.text
    with db_session() as db:
        assert db.get(EmailChallenge, "12345678") is None


def test_session_expiry_and_qq_change_revoke(private_client):
    client, sent = private_client
    send(client)
    assert login(client, sent).status_code == 200
    visitor_token = client.cookies.get(COOKIE)
    assert (
        client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "test-only-password-2026"},
        ).status_code
        == 200
    )
    assert (
        client.patch("/api/admin/site", json={"boy_qq": "23456789"}).status_code == 200
    )
    client.cookies.clear()
    client.cookies.set(COOKIE, visitor_token)
    assert client.get("/api/visitor/me").status_code == 401
    assert login(client, sent).status_code == 400
    send(client, "87654321@qq.com")
    assert login(client, sent).status_code == 200
    with db_session() as db:
        session = db.query(VisitorSession).one()
        session.expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    assert client.get("/api/site").status_code == 401


def test_upload_requires_session(admin, monkeypatch):
    sent = []
    monkeypatch.setattr(
        mail, "send_login_code", lambda email, code, db: sent.append((email, code))
    )
    admin.patch("/api/admin/site", json={"boy_qq": "12345678"})
    image = BytesIO()
    Image.new("RGB", (10, 10)).save(image, format="PNG")
    url = admin.post(
        "/api/admin/upload", files={"file": ("x.png", image.getvalue(), "image/png")}
    ).json()["url"]
    assert admin.get(url).status_code == 200
    admin.cookies.clear()
    assert admin.get(url).status_code == 401
    send(admin)
    login(admin, sent)
    response = admin.get(url)
    assert (
        response.status_code == 200 and "no-store" in response.headers["cache-control"]
    )
    assert admin.get("/uploads/not-a-file.webp").status_code == 404


def test_email_origin_protection(private_client):
    client, sent = private_client
    assert (
        client.post(
            "/api/visitor/code",
            json={"email": "12345678@qq.com"},
            headers={"Origin": "https://other.example"},
        ).status_code
        == 403
    )
    assert sent == []
