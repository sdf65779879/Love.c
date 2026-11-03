import hashlib
import logging
from datetime import UTC, datetime, timedelta
from threading import Event, Thread
from zoneinfo import ZoneInfo

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from . import mail
from .database import SessionLocal
from .mail_letter import anniversary_letter
from .memories import anniversary_days
from .models import Anniversary, MailDelivery, MailSettings, SiteSettings

SHANGHAI = ZoneInfo("Asia/Shanghai")
EVENT = "ANNIVERSARY_REMINDER"
logger = logging.getLogger("uvicorn.error")


def reserve(db, key, email, stamp):
    row = db.scalar(select(MailDelivery).where(MailDelivery.reminder_key == key))
    if row is None:
        row = MailDelivery(
            reminder_key=key,
            event=EVENT,
            recipient=mail.masked(email),
            status="sending",
            actor="系统",
            detail="正在提交纪念日提醒",
            created_at=stamp,
        )
        db.add(row)
        try:
            db.commit()  # The unique key must be durable before contacting SMTP.
        except IntegrityError:
            db.rollback()
            return None
        return row
    if row.status != "failed" or row.created_at > stamp - timedelta(hours=1):
        return None
    claim = db.execute(
        update(MailDelivery)
        .where(
            MailDelivery.id == row.id,
            MailDelivery.status == "failed",
            MailDelivery.created_at <= stamp - timedelta(hours=1),
        )
        .values(status="sending", created_at=stamp)
    )
    db.commit()
    return row if claim.rowcount == 1 else None


def check_reminders(db, now=None):
    now = datetime.now(SHANGHAI) if now is None else now.astimezone(SHANGHAI)
    if now.hour < 9:
        return
    today = now.date()
    occasion = today + timedelta(days=2)
    config = db.get(MailSettings, 1)
    site = db.get(SiteSettings, 1)
    if not (
        config
        and config.enabled
        and config.username
        and config.encrypted_password
        and site
    ):
        return
    recipients = {
        qq: name
        for qq, name in [(site.boy_qq, site.boy_name), (site.girl_qq, site.girl_name)]
        if qq
    }
    for item in db.scalars(select(Anniversary)).all():
        if anniversary_days(item.date, item.annual, today)["days_until"] != 2:
            continue
        for qq, name in recipients.items():
            email = f"{qq}@qq.com"
            key = hashlib.sha256(f"{item.id}/{occasion}/{email}".encode()).hexdigest()
            record = reserve(db, key, email, now.astimezone(UTC).replace(tzinfo=None))
            if record is None:
                continue
            try:
                mail.deliver(
                    db,
                    email,
                    EVENT,
                    "LOVE.C · 两天后的纪念日",
                    anniversary_letter(name, item.title, occasion),
                    record=record,
                )
                db.commit()
            except mail.MailError:
                # deliver persisted the outcome. Continue with the other recipient.
                continue


def start_reminders():
    stop = Event()

    def loop():
        while not stop.is_set():
            try:
                with SessionLocal() as db:
                    check_reminders(db)
            except Exception:
                logger.error(
                    "Anniversary reminder scan failed; will check again in one minute"
                )
            stop.wait(60)

    thread = Thread(target=loop, name="anniversary-reminders", daemon=True)
    thread.start()
    return stop, thread
