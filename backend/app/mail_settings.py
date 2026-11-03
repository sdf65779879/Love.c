import re
from datetime import UTC
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr, Field, SecretStr, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import mail
from .database import get_db
from .mail_letter import couple_letter
from .models import MailDelivery, MailSettings, SiteSettings, User, utcnow
from .schemas import Input
from .secrets import encrypt_secret
from .security import current_user, limiter

router = APIRouter(prefix="/api/admin/mail", dependencies=[Depends(current_user)])


class MailInput(Input):
    enabled: bool
    host: str = Field(min_length=1, max_length=253)
    port: int = Field(ge=1, le=65535)
    username: EmailStr
    from_address: EmailStr | Literal[""] = ""
    security: Literal["ssl", "starttls"]
    password: SecretStr | None = None

    @field_validator("password")
    @classmethod
    def password_length(cls, value):
        if value and len(value.get_secret_value()) > 500:
            raise ValueError("授权码长度不能超过 500 个字符")
        return value

    @field_validator("host")
    @classmethod
    def hostname(cls, value):
        if not re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?", value):
            raise ValueError("请输入 SMTP 主机名，不要包含协议、路径或空格")
        return value.lower()


class TestInput(Input):
    partner: Literal["boy", "girl"]


def public_config(record):
    return {
        **{
            key: getattr(record, key)
            for key in (
                "enabled",
                "host",
                "port",
                "username",
                "from_address",
                "security",
            )
        },
        "has_password": bool(record.encrypted_password),
        "updated_at": record.updated_at.replace(tzinfo=UTC),
    }


@router.get("")
def get_settings(db: Session = Depends(get_db)):
    return public_config(db.get(MailSettings, 1))


@router.put("")
def save_settings(
    data: MailInput, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    record = db.get(MailSettings, 1, with_for_update=True)
    password = data.password.get_secret_value() if data.password else ""
    if data.username != record.username and not password:
        raise HTTPException(422, "更换发件邮箱时，请同时填写对应的新授权码")
    if data.enabled and not (password or record.encrypted_password):
        raise HTTPException(422, "启用系统邮箱前，请填写 SMTP 授权码")
    for key, value in data.model_dump(exclude={"password"}).items():
        setattr(
            record, key, str(value) if key in {"username", "from_address"} else value
        )
    if password:
        record.encrypted_password = encrypt_secret(password)
    record.updated_at = utcnow()
    db.add(
        MailDelivery(
            event="SETTINGS_UPDATED",
            recipient=mail.masked(record.username),
            status="saved",
            detail="邮箱配置已更新",
            actor=user.username,
        )
    )
    db.commit()
    return public_config(record)


@router.post("/test")
def test_delivery(
    data: TestInput, db: Session = Depends(get_db), user: User = Depends(current_user)
):
    limiter.check(f"mail-test:{user.id}", 3, 300)
    site = db.get(SiteSettings, 1)
    qq = getattr(site, f"{data.partner}_qq")
    if not qq:
        raise HTTPException(422, "请先在情侣配置中填写该方 QQ 号")
    try:
        mail.deliver(
            db,
            f"{qq}@qq.com",
            "SMTP_TEST",
            "LOVE.C 系统邮箱测试",
            couple_letter(getattr(site, f"{data.partner}_name")),
            user.username,
        )
    except mail.MailError as error:
        raise HTTPException(503, str(error)) from None
    db.commit()
    return {"message": "测试邮件已提交到邮件服务器，请检查收件箱或垃圾邮件"}


@router.get("/deliveries")
def deliveries(db: Session = Depends(get_db)):
    rows = db.scalars(
        select(MailDelivery).order_by(MailDelivery.id.desc()).limit(30)
    ).all()
    return [
        {
            **{
                key: getattr(row, key)
                for key in ("id", "event", "recipient", "status", "detail", "actor")
            },
            "created_at": row.created_at.replace(tzinfo=UTC),
        }
        for row in rows
    ]
