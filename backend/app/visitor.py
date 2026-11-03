import hashlib
import hmac
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import Field, field_validator
from sqlalchemy import delete
from sqlalchemy.orm import Session

from . import mail
from .config import settings
from .database import get_db
from .models import EmailChallenge, SiteSettings, VisitorSession, utcnow
from .schemas import Input
from .security import current_user, limiter

router = APIRouter(prefix="/api/visitor")
COOKIE = "love_visitor"


class EmailInput(Input):
    email: str = Field(pattern=r"^[1-9][0-9]{4,10}@qq\.com$")

    @field_validator("email", mode="before")
    @classmethod
    def normalize(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class VerifyInput(EmailInput):
    code: str = Field(pattern=r"^[0-9]{6}$")


def digest(value: str) -> str:
    return hmac.new(
        settings.secret_key.encode(), value.encode(), hashlib.sha256
    ).hexdigest()


def allowed_qq(site):
    return {qq for qq in (site.boy_qq, site.girl_qq) if qq}


def current_visitor(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE, "")
    session = db.get(VisitorSession, digest(token)) if token else None
    if (
        not session
        or session.expires_at <= utcnow()
        or session.qq not in allowed_qq(db.get(SiteSettings, 1))
    ):
        raise HTTPException(401, "请使用情侣 QQ 邮箱验证后进入小站")
    return session


def current_viewer(request: Request, db: Session = Depends(get_db)):
    # Administrators still need access to settings and uploaded media in the console.
    try:
        return current_visitor(request, db)
    except HTTPException:
        return current_user(request, db)


def invalidate_visitors(db: Session):
    db.execute(delete(VisitorSession))
    db.execute(delete(EmailChallenge))


@router.post("/code")
def request_code(data: EmailInput, request: Request, db: Session = Depends(get_db)):
    limiter.check(f"email-send:{request.client.host}", 10, 3600)
    # One persistent lock serializes sends, verification and changes to the allowlist.
    site = db.get(SiteSettings, 1, with_for_update=True)
    qq = data.email.split("@")[0]
    generic = {
        "message": "如果该邮箱属于小站主人，验证码将发送至邮箱，请查收。",
        "retry_after": 60,
    }
    if qq not in allowed_qq(site):
        return generic
    now = utcnow()
    challenge = db.get(EmailChallenge, qq)
    if challenge:
        if now - challenge.sent_at < timedelta(seconds=60):
            raise HTTPException(
                429, "请等待 60 秒后再发送", headers={"Retry-After": "60"}
            )
        if (
            now - challenge.period_start < timedelta(hours=1)
            and challenge.send_count >= 5
        ):
            raise HTTPException(429, "该邮箱发送次数已达上限，请稍后再试")
    code = f"{secrets.randbelow(1000000):06d}"
    nonce = secrets.token_hex(16)
    try:
        mail.send_login_code(data.email, code, db)
    except Exception:
        raise HTTPException(
            503, "验证码发送失败，请稍后重试；管理员请检查发件邮箱配置"
        ) from None
    if not challenge:
        challenge = EmailChallenge(qq=qq, period_start=now, send_count=0)
        db.add(challenge)
    if now - challenge.period_start >= timedelta(hours=1):
        challenge.period_start, challenge.send_count = now, 0
    challenge.send_count += 1
    challenge.sent_at = now
    challenge.expires_at = now + timedelta(minutes=5)
    challenge.attempts = 0
    challenge.nonce = nonce
    challenge.digest = digest(f"{qq}:{nonce}:{code}")
    db.commit()
    return generic


@router.post("/login")
def verify_code(
    data: VerifyInput,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    limiter.check(f"email-verify:{request.client.host}", 20, 300)
    site = db.get(SiteSettings, 1, with_for_update=True)
    qq = data.email.split("@")[0]
    challenge = db.get(EmailChallenge, qq)
    error = HTTPException(400, "验证码不正确或已过期，请重新获取")
    if (
        qq not in allowed_qq(site)
        or not challenge
        or challenge.expires_at <= utcnow()
        or challenge.attempts >= 5
    ):
        raise error
    challenge.attempts += 1
    if not hmac.compare_digest(
        challenge.digest, digest(f"{qq}:{challenge.nonce}:{data.code}")
    ):
        db.commit()
        raise error
    challenge.expires_at = (
        utcnow()
    )  # Consume once while preserving delivery rate limits.
    token = secrets.token_urlsafe(32)
    db.execute(delete(VisitorSession).where(VisitorSession.expires_at <= utcnow()))
    old_token = request.cookies.get(COOKIE)
    if old_token:
        db.execute(
            delete(VisitorSession).where(VisitorSession.digest == digest(old_token))
        )
    db.add(
        VisitorSession(
            digest=digest(token), qq=qq, expires_at=utcnow() + timedelta(hours=12)
        )
    )
    db.commit()
    response.set_cookie(
        COOKIE,
        token,
        max_age=43200,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/",
    )
    return {"message": "验证成功，欢迎回家"}


@router.get("/me")
def me(session: VisitorSession = Depends(current_visitor)):
    return {"authenticated": True}


@router.get("/access", dependencies=[Depends(current_viewer)])
def access():
    return {"authenticated": True}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE, "")
    db.execute(delete(VisitorSession).where(VisitorSession.digest == digest(token)))
    db.commit()
    response.delete_cookie(
        COOKIE,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
    )
    return {"message": "已退出小站"}
