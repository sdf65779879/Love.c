import smtplib
from unittest.mock import MagicMock

import pytest
from app import mail
from app.database import get_db
from app.mail_letter import couple_letter
from app.main import app
from app.models import MailSettings
from app.secrets import decrypt_secret


def configuration(**changes):
    return {
        "enabled": True,
        "host": "smtp.qq.com",
        "port": 465,
        "username": "12345678@qq.com",
        "from_address": "",
        "security": "ssl",
        "password": "test-only-authorization-code",
        **changes,
    }


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/admin/mail"),
        ("put", "/api/admin/mail"),
        ("post", "/api/admin/mail/test"),
        ("get", "/api/admin/mail/deliveries"),
    ],
)
def test_mail_admin_only(client, method, path):
    assert getattr(client, method)(path).status_code == 401


def test_encryption_preserve_and_redaction(admin):
    secret = configuration()["password"]
    result = admin.put("/api/admin/mail", json=configuration())
    assert result.status_code == 200 and result.json()["has_password"]
    assert secret not in result.text and "encrypted_password" not in result.text
    with next(app.dependency_overrides[get_db]()) as db:
        stored = db.get(MailSettings, 1).encrypted_password
        assert stored != secret and decrypt_secret(stored) == secret
    result = admin.put(
        "/api/admin/mail",
        json=configuration(password="", port=587, security="starttls"),
    )
    assert result.status_code == 200
    with next(app.dependency_overrides[get_db]()) as db:
        assert db.get(MailSettings, 1).encrypted_password == stored
    assert secret not in admin.get("/api/admin/mail").text
    assert secret not in admin.get("/api/admin/mail/deliveries").text
    assert (
        admin.put(
            "/api/admin/mail",
            json=configuration(username="87654321@qq.com", password=""),
        ).status_code
        == 422
    )


def test_mail_validation_never_echoes_secret(admin):
    for changes in [
        {"password": "secret" * 100},
        {"host": "https://smtp.qq.com"},
        {"security": "none"},
        {"port": 0},
        {"username": "bad\r\nBcc:x@y.com"},
    ]:
        data = configuration(**changes)
        result = admin.put("/api/admin/mail", json=data)
        assert result.status_code == 422
        assert data["password"] not in result.text and '"input"' not in result.text


def test_latest_configuration_and_delivery_records(admin, monkeypatch):
    admin.patch("/api/admin/site", json={"boy_qq": "12345678", "girl_qq": "87654321"})
    captured = []
    monkeypatch.setattr(
        mail,
        "smtp_send",
        lambda config, recipient, subject, body: captured.append(
            (config.host, recipient, subject, body)
        ),
    )
    admin.put("/api/admin/mail", json=configuration())
    assert (
        admin.post("/api/admin/mail/test", json={"partner": "boy"}).status_code == 200
    )
    admin.put(
        "/api/admin/mail", json=configuration(host="smtp.example.com", password="")
    )
    assert (
        admin.post("/api/admin/mail/test", json={"partner": "girl"}).status_code == 200
    )
    assert captured[0][:2] == ("smtp.qq.com", "12345678@qq.com")
    assert captured[1][:2] == ("smtp.example.com", "87654321@qq.com")
    records = admin.get("/api/admin/mail/deliveries").json()
    assert records[0]["status"] == "sent"
    assert "87654321" not in str(records)
    # The login flow reads the same saved mailbox and records delivery safely.
    assert (
        admin.post("/api/visitor/code", json={"email": "12345678@qq.com"}).status_code
        == 200
    )
    assert captured[-1][0] == "smtp.example.com"
    records = admin.get("/api/admin/mail/deliveries").json()
    assert records[0]["event"] == "LOGIN_CODE"
    assert "body" not in records[0] and "code" not in records[0]


def test_provider_failure_audit_and_disable(admin, monkeypatch):
    admin.patch("/api/admin/site", json={"boy_qq": "12345678"})
    admin.put("/api/admin/mail", json=configuration())

    def fail(*args):
        raise RuntimeError("private-smtp-password-and-provider-response")

    with monkeypatch.context() as patch:
        patch.setattr(mail, "smtp_send", fail)
        response = admin.post("/api/admin/mail/test", json={"partner": "boy"})
        assert response.status_code == 503 and "private-smtp" not in response.text
    rows = admin.get("/api/admin/mail/deliveries").json()
    assert rows[0]["status"] == "failed" and "private-smtp" not in str(rows)
    admin.put("/api/admin/mail", json=configuration(enabled=False, password=""))
    response = admin.post("/api/admin/mail/test", json={"partner": "boy"})
    assert response.status_code == 503 and "停用" in response.text


@pytest.mark.parametrize("security", ["ssl", "starttls"])
def test_provider_tls_and_safe_auth_error(admin, monkeypatch, security):
    admin.put("/api/admin/mail", json=configuration(security=security))
    smtp = MagicMock()
    smtp.__enter__.return_value = smtp
    smtp.send_message.return_value = {}
    factory = MagicMock(return_value=smtp)
    monkeypatch.setattr(
        mail.smtplib, "SMTP_SSL" if security == "ssl" else "SMTP", factory
    )
    with next(app.dependency_overrides[get_db]()) as db:
        config = db.get(MailSettings, 1)
        letter = couple_letter("<小满>", code="001234")
        mail.smtp_send(config, "87654321@qq.com", "Test", letter)
        message = smtp.send_message.call_args.args[0]
        assert message.get_content_type() == "multipart/alternative"
        for mime, greeting in [("plain", "<小满>"), ("html", "&lt;小满&gt;")]:
            body = message.get_body(preferencelist=(mime,)).get_content()
            assert greeting in body and body.count("001234") == 1
            assert "5 分钟" in body and "仅可使用一次" in body
        assert factory.call_args.kwargs["timeout"] == 12
        if security == "starttls":
            smtp.starttls.assert_called_once()
        else:
            assert "context" in factory.call_args.kwargs
        smtp.login.assert_called_with("12345678@qq.com", "test-only-authorization-code")
        smtp.login.side_effect = smtplib.SMTPAuthenticationError(
            535, b"sensitive provider details"
        )
        with pytest.raises(mail.MailError, match="认证失败") as error:
            mail.smtp_send(config, "87654321@qq.com", "Test", letter)
        assert "sensitive" not in str(error.value)


def test_missing_receiver_and_test_limit(admin, monkeypatch):
    admin.put("/api/admin/mail", json=configuration())
    monkeypatch.setattr(mail, "smtp_send", lambda *args: None)
    assert (
        admin.post("/api/admin/mail/test", json={"partner": "boy"}).status_code == 422
    )
    admin.patch("/api/admin/site", json={"boy_qq": "12345678"})
    for _ in range(2):
        assert (
            admin.post("/api/admin/mail/test", json={"partner": "boy"}).status_code
            == 200
        )
    assert (
        admin.post("/api/admin/mail/test", json={"partner": "boy"}).status_code == 429
    )
