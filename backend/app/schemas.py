from datetime import date as DateValue
from datetime import datetime
from typing import Annotated, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Input(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class MediaInput(Input):
    @field_validator("image", "cover", "boy_avatar", "girl_avatar", check_fields=False)
    @classmethod
    def safe_media(cls, value: str) -> str:
        if value and not (
            value.startswith(("https://", "http://"))
            or (
                value.startswith(("/images/", "/uploads/"))
                and ".." not in value
                and "\\" not in value
            )
        ):
            raise ValueError("请使用 HTTP(S) 图片地址或已上传的图片路径")
        return value


Title = Annotated[str, Field(min_length=1, max_length=150)]
Media = Annotated[str, Field(max_length=500)]


class LoginInput(Input):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=200)


class PasswordInput(Input):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=12, max_length=200)


class SettingsInput(MediaInput):
    boy_qq: str = Field(default="", pattern=r"^(?:[1-9][0-9]{4,10})?$")
    girl_qq: str = Field(default="", pattern=r"^(?:[1-9][0-9]{4,10})?$")
    logo_text: str = Field(default="", max_length=80)
    avatar_blur: bool = True
    card_titles: dict[
        Literal["/moments", "/messages", "/about", "/album", "/wishlist", "/gifts"],
        Annotated[str, Field(min_length=1, max_length=30)],
    ] = Field(default_factory=dict)
    title: str = Field(min_length=1, max_length=80)
    subtitle: str = Field(max_length=200)
    boy_name: str = Field(min_length=1, max_length=30)
    girl_name: str = Field(min_length=1, max_length=30)
    boy_avatar: Media
    girl_avatar: Media
    cover: Media
    start_date: datetime
    about_intro: str = Field(min_length=1, max_length=3000)
    about_story: str = Field(min_length=1, max_length=5000)
    about_future: str = Field(min_length=1, max_length=5000)
    footer_text: str = Field(max_length=200)
    icp: str = Field(max_length=100)
    messages_enabled: bool

    @field_validator("start_date")
    @classmethod
    def normalize_date(cls, value: datetime) -> datetime:
        # Store wall-clock time in Asia/Shanghai; the public API supplies +08:00.
        if value.tzinfo:
            value = value.astimezone(ZoneInfo("Asia/Shanghai")).replace(tzinfo=None)
        if value > datetime.now(ZoneInfo("Asia/Shanghai")).replace(tzinfo=None):
            raise ValueError("相恋时间不能晚于现在")
        return value


class ArticleInput(MediaInput):
    title: Title
    content: str = Field(min_length=1, max_length=50000)
    author: str = Field(min_length=1, max_length=40)
    date: DateValue
    cover: Media = ""
    published: bool = True


class PhotoInput(MediaInput):
    title: Title
    image: str = Field(min_length=1, max_length=500)
    date: DateValue
    location: str = Field(max_length=100, default="")


class WishInput(MediaInput):
    title: Title
    completed: bool = False
    date: DateValue | None = None
    image: Media = ""


class GiftInput(MediaInput):
    title: Title
    description: str = Field(min_length=1, max_length=3000)
    sender: str = Field(min_length=1, max_length=40)
    date: DateValue
    image: Media = ""


class MessageInput(Input):
    name: str = Field(min_length=1, max_length=40)
    content: str = Field(min_length=1, max_length=1000)
    website: str = Field(default="", max_length=500)


class ModerationInput(Input):
    approved: bool
