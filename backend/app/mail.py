import smtplib
import ssl
from email.message import EmailMessage

from cryptography.fernet import InvalidToken
from email_validator import validate_email

from .mail_letter import Letter, couple_letter
from .models import MailDelivery, MailSettings, SiteSettings
from .secrets import decrypt_secret


class MailError(Exception):
    """Safe message only; SMTP responses and secrets never leave the provider."""


class MailUncertain(MailError):
    """A connection failed after submission began; the server may have accepted it."""


def masked(email: str) -> str:
    local, _, domain = email.partition("@")
    return f"{local[:2]}***@{domain}" if domain else "未设置"


def smtp_send(config: MailSettings, recipient: str, subject: str, body: Letter):
    if not config.enabled:
        raise MailError("系统邮箱已停用，请在后台启用")
    if not config.username or not config.encrypted_password:
        raise MailError("请先配置发件邮箱和 SMTP 授权码")
    try:
        password = decrypt_secret(config.encrypted_password)
    except InvalidToken:
        raise MailError("授权码无法解密，请重新保存授权码并检查 SECRET_KEY") from None
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config.from_address or config.username
    message["To"] = recipient
    message.set_content(body.text)
    message.add_alternative(body.html, subtype="html")
    context = ssl.create_default_context()
    submitting = False
    accepted = False
    try:
        if config.security == "ssl":
            connection = smtplib.SMTP_SSL(
                config.host, config.port, timeout=12, context=context
            )
        elif config.security == "starttls":
            connection = smtplib.SMTP(config.host, config.port, timeout=12)
            try:
                connection.starttls(context=context)
            except Exception:
                connection.close()
                raise
        else:
            raise MailError("请选择 SSL/TLS 或 STARTTLS 加密方式")
        with connection as smtp:
            smtp.login(config.username, password)
            submitting = True
            refused = smtp.send_message(message)
            if refused:
                raise MailError("收件地址被拒绝，请检查邮箱地址")
            accepted = True
    except smtplib.SMTPAuthenticationError:
        raise MailError(
            "邮箱认证失败，请检查发件账号、SMTP 授权码及 SMTP 服务开关"
        ) from None
    except smtplib.SMTPRecipientsRefused:
        raise MailError("收件地址被拒绝，请检查邮箱地址") from None
    except smtplib.SMTPSenderRefused:
        raise MailError("发件地址被拒绝，请确认发件地址与邮箱账号匹配") from None
    except (smtplib.SMTPException, OSError) as error:
        if accepted:
            return  # A failed QUIT does not undo a successful DATA response.
        if submitting and not isinstance(error, smtplib.SMTPResponseException):
            raise MailUncertain("邮件提交结果未确认，请检查收件箱") from None
        raise MailError(
            "邮件服务连接或投递失败，请检查服务器、端口及加密方式后重试"
        ) from None


def deliver(
    db,
    recipient: str,
    event: str,
    subject: str,
    body: Letter,
    actor: str = "",
    *,
    record: MailDelivery | None = None,
):
    """One attempt per request; uncertain delivery is never automatically retried."""
    recipient = validate_email(recipient, check_deliverability=False).normalized
    record = record or MailDelivery(
        event=event, recipient=masked(recipient), status="sending", actor=actor
    )
    db.add(record)
    config = db.get(MailSettings, 1, populate_existing=True)
    try:
        if not config:
            raise MailError("请先保存系统邮箱配置")
        smtp_send(config, recipient, subject, body)
    except Exception as error:
        safe_error = (
            str(error)
            if isinstance(error, MailError)
            else "邮件发送失败，请检查邮箱配置后重试"
        )
        record.status = "uncertain" if isinstance(error, MailUncertain) else "failed"
        record.detail = safe_error
        db.commit()
        raise MailError(safe_error) from None
    record.status, record.detail = "sent", "已提交到邮件服务器，请检查收件箱或垃圾邮件"


def send_login_code(email: str, code: str, db):
    site = db.get(SiteSettings, 1)
    name = site.boy_name if email == f"{site.boy_qq}@qq.com" else site.girl_name
    deliver(
        db,
        email,
        "LOGIN_CODE",
        "LOVE.C 登录验证码",
        couple_letter(name, code=code),
    )
