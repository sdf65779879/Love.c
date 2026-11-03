from datetime import UTC, date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Integer, String, Text
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    token_version: Mapped[int] = mapped_column(Integer, default=0)


class EmailChallenge(Base):
    __tablename__ = "email_challenges"
    qq: Mapped[str] = mapped_column(String(11), primary_key=True)
    digest: Mapped[str] = mapped_column(String(64))
    nonce: Mapped[str] = mapped_column(String(32))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    sent_at: Mapped[datetime] = mapped_column(DateTime)
    period_start: Mapped[datetime] = mapped_column(DateTime)
    send_count: Mapped[int] = mapped_column(Integer)
    attempts: Mapped[int] = mapped_column(Integer, default=0)


class MailSettings(Base):
    __tablename__ = "mail_settings"
    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    host: Mapped[str] = mapped_column(String(253), default="smtp.qq.com")
    port: Mapped[int] = mapped_column(Integer, default=465)
    username: Mapped[str] = mapped_column(String(254), default="")
    from_address: Mapped[str] = mapped_column(String(254), default="")
    security: Mapped[str] = mapped_column(String(10), default="ssl")
    encrypted_password: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class MailDelivery(Base):
    __tablename__ = "mail_deliveries"
    reminder_key: Mapped[str | None] = mapped_column(String(64), unique=True)
    id: Mapped[int] = mapped_column(primary_key=True)
    event: Mapped[str] = mapped_column(String(30))
    recipient: Mapped[str] = mapped_column(String(254))
    status: Mapped[str] = mapped_column(String(20))
    detail: Mapped[str] = mapped_column(String(200), default="")
    actor: Mapped[str] = mapped_column(String(50), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class VisitorSession(Base):
    __tablename__ = "visitor_sessions"
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    qq: Mapped[str] = mapped_column(String(11))
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class SiteSettings(Base):
    __tablename__ = "site_settings"
    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    title: Mapped[str] = mapped_column(String(80), default="LOVE.C")
    logo_text: Mapped[str] = mapped_column(String(80), default="")
    avatar_blur: Mapped[bool] = mapped_column(Boolean, default=True)
    background_theme: Mapped[str] = mapped_column(String(16), default="cream")
    card_titles: Mapped[dict] = mapped_column(JSON, default=dict)
    subtitle: Mapped[str] = mapped_column(
        String(200), default="喜欢花，喜欢浪漫，也喜欢你。"
    )
    boy_name: Mapped[str] = mapped_column(String(30), default="阿辰")
    boy_qq: Mapped[str] = mapped_column(String(11), default="")
    girl_qq: Mapped[str] = mapped_column(String(11), default="")
    girl_name: Mapped[str] = mapped_column(String(30), default="小满")
    boy_avatar: Mapped[str] = mapped_column(String(500), default="/images/boy.svg")
    girl_avatar: Mapped[str] = mapped_column(String(500), default="/images/girl.svg")
    cover: Mapped[str] = mapped_column(String(500), default="/images/cover.png")
    start_date: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime(2024, 5, 20)
    )
    about_intro: Mapped[str] = mapped_column(
        Text,
        default="你好呀，欢迎来到我们的秘密花园。\n这里收藏着两个人平凡又闪闪发光的日常。",
    )
    about_story: Mapped[str] = mapped_column(
        Text,
        default="我们的故事，始于一次不经意的遇见。\n从一句你好，到每天的早安和晚安。\n慢慢来吧，想和你一起走的路还很长。",
    )
    about_future: Mapped[str] = mapped_column(
        Text,
        default="一起去看海，一起等日落。\n把柴米油盐的日子，也过成喜欢的样子。\n愿得一心人，白头不相离。",
    )
    footer_text: Mapped[str] = mapped_column(
        String(200), default="把心动写进生活，把你写进余生。"
    )
    icp: Mapped[str] = mapped_column(String(100), default="")
    messages_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class Article(Base):
    __tablename__ = "articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    content: Mapped[str] = mapped_column(Text().with_variant(MEDIUMTEXT(), "mysql"))
    author: Mapped[str] = mapped_column(String(40))
    date: Mapped[date] = mapped_column(Date)
    cover: Mapped[str] = mapped_column(String(500), default="")
    published: Mapped[bool] = mapped_column(Boolean, default=True)


class Photo(Base):
    __tablename__ = "photos"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    image: Mapped[str] = mapped_column(String(500))
    date: Mapped[date] = mapped_column(Date)
    location: Mapped[str] = mapped_column(String(100), default="")


class Wish(Base):
    __tablename__ = "wishes"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    date: Mapped[date | None] = mapped_column(Date, nullable=True)
    image: Mapped[str] = mapped_column(String(500), default="")


class Gift(Base):
    __tablename__ = "gifts"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    image: Mapped[str] = mapped_column(String(500), default="")
    sender: Mapped[str] = mapped_column(String(40))
    date: Mapped[date] = mapped_column(Date)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40))
    content: Mapped[str] = mapped_column(String(1000))
    approved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Place(Base):
    __tablename__ = "places"
    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(150))
    date: Mapped[date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(Text, default="")
    image: Mapped[str] = mapped_column(String(500), default="")


class Anniversary(Base):
    __tablename__ = "anniversaries"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    date: Mapped[date] = mapped_column(Date)
    annual: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str] = mapped_column(Text, default="")
