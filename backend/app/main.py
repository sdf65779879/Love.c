import re
import warnings
from contextlib import asynccontextmanager
from datetime import UTC
from io import BytesIO
from uuid import uuid4

from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import ValidationError
from sqlalchemy import func, select, text
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

from .config import settings
from .database import engine, get_db
from .mail_settings import router as mail_router
from .models import Article, Gift, Message, Photo, SiteSettings, User, Wish
from .schemas import (
    ArticleInput,
    GiftInput,
    LoginInput,
    MessageInput,
    ModerationInput,
    PasswordInput,
    PhotoInput,
    SettingsInput,
    WishInput,
)
from .security import current_user, dummy_hash, limiter, password_hash, token_for
from .seed import seed
from .visitor import current_viewer, invalidate_visitors
from .visitor import router as visitor_router


@asynccontextmanager
async def lifespan(app):
    seed()
    yield


app = FastAPI(
    title="LOVE.C · 两个人的小世界",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)
settings.upload_dir.mkdir(parents=True, exist_ok=True)
app.include_router(visitor_router)
app.include_router(mail_router)


@app.exception_handler(RequestValidationError)
async def safe_validation_error(request, error):
    # Validation errors must not echo passwords, OTPs or SMTP credentials.
    return JSONResponse(
        status_code=422,
        content={
            "detail": [
                {key: item[key] for key in ("loc", "msg", "type") if key in item}
                for item in error.errors()
            ]
        },
    )


@app.get("/uploads/{filename}", dependencies=[Depends(current_viewer)])
def private_upload(filename: str):
    if not re.fullmatch(r"[a-f0-9]{32}\.webp", filename):
        raise HTTPException(404, "图片不存在")
    path = settings.upload_dir / filename
    if not path.is_file():
        raise HTTPException(404, "图片不存在")
    return FileResponse(path, headers={"Cache-Control": "private, no-store"})


@app.middleware("http")
async def protect_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    if (
        request.method in {"POST", "PUT", "PATCH", "DELETE"}
        and origin
        and origin.rstrip("/") not in settings.origins
    ):
        from fastapi.responses import JSONResponse

        return JSONResponse(
            {"detail": "请求来源未授权，请检查 CORS_ORIGINS 配置"}, status_code=403
        )
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.url.path.startswith(("/api/", "/uploads/")):
        response.headers["Cache-Control"] = "no-store"
    return response


def serialize(obj):
    data = {
        column.key: getattr(obj, column.key)
        for column in inspect(obj).mapper.column_attrs
    }
    if isinstance(obj, Message):
        data["created_at"] = obj.created_at.replace(tzinfo=UTC)
    return jsonable_encoder(data)


def get_record(db, model, record_id):
    record = db.get(model, record_id)
    if not record:
        raise HTTPException(404, "内容不存在或已删除")
    return record


def page_result(db, model, page, page_size, conditions=()):
    total = db.scalar(select(func.count()).select_from(model).where(*conditions))
    rows = db.scalars(
        select(model)
        .where(*conditions)
        .order_by(
            *(
                [model.date.desc(), model.id.desc()]
                if model in (Article, Photo, Gift)
                else [model.id.desc()]
            )
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "items": [serialize(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": engine.dialect.name}


@app.get("/api/site", dependencies=[Depends(current_viewer)])
def site(db: Session = Depends(get_db)):
    data = serialize(db.get(SiteSettings, 1))
    data["start_date"] += "+08:00"
    data["source_url"] = settings.source_url
    data["stats"] = {
        kind: db.scalar(select(func.count()).select_from(model).where(*conditions))
        for kind, model, conditions in [
            ("articles", Article, (Article.published.is_(True),)),
            ("photos", Photo, ()),
            ("wishes", Wish, ()),
            ("completed", Wish, (Wish.completed.is_(True),)),
            ("gifts", Gift, ()),
        ]
    }
    return data


@app.get("/api/articles/{article_id}", dependencies=[Depends(current_viewer)])
def article(article_id: int, db: Session = Depends(get_db)):
    record = get_record(db, Article, article_id)
    if not record.published:
        raise HTTPException(404, "内容不存在或已删除")
    return serialize(record)


PUBLIC_MODELS = {
    "articles": Article,
    "photos": Photo,
    "wishes": Wish,
    "gifts": Gift,
    "messages": Message,
}


@app.get("/api/content/{kind}", dependencies=[Depends(current_viewer)])
def public_content(
    kind: str,
    page: int = Query(1, ge=1, le=100000),
    page_size: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db),
):
    model = PUBLIC_MODELS.get(kind)
    if not model:
        raise HTTPException(404, "内容类型不存在")
    conditions = (
        (Article.published.is_(True),)
        if kind == "articles"
        else (Message.approved.is_(True),)
        if kind == "messages"
        else ()
    )
    result = page_result(db, model, page, page_size, conditions)
    if kind == "articles":
        for item in result["items"]:
            item["excerpt"] = item.pop("content")[:160]
    return result


@app.post("/api/messages", status_code=201, dependencies=[Depends(current_viewer)])
def leave_message(data: MessageInput, request: Request, db: Session = Depends(get_db)):
    if not db.get(SiteSettings, 1).messages_enabled:
        raise HTTPException(403, "留言板暂时休息中")
    limiter.check(f"message:{request.client.host}", 3, 300)
    if data.website:
        raise HTTPException(400, "留言未通过校验")
    record = Message(name=data.name, content=data.content)
    db.add(record)
    db.commit()
    return {"message": "祝福已送达，审核通过后会显示在留言板。"}


@app.post("/api/auth/login")
def login(
    data: LoginInput,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    limiter.check(f"login:{request.client.host}", 10, 300)
    user = db.scalar(select(User).where(User.username == data.username))
    valid = password_hash.verify(
        data.password, user.password_hash if user else dummy_hash
    )
    if not user or not valid:
        raise HTTPException(401, "账号或密码不正确")
    response.set_cookie(
        "session",
        token_for(user),
        max_age=43200,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/",
    )
    return {"username": user.username}


@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return {"username": user.username}


@app.post("/api/auth/logout")
def logout(
    response: Response,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    user.token_version += 1
    db.commit()
    response.delete_cookie(
        "session",
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="strict",
    )
    return {"message": "已退出登录"}


@app.post("/api/auth/password")
def change_password(
    data: PasswordInput,
    response: Response,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if not password_hash.verify(data.current_password, user.password_hash):
        raise HTTPException(400, "当前密码不正确")
    user.password_hash = password_hash.hash(data.new_password)
    user.token_version += 1
    db.commit()
    response.delete_cookie("session", path="/")
    return {"message": "密码已修改，请重新登录"}


@app.put("/api/admin/site", dependencies=[Depends(current_user)])
def update_site(data: SettingsInput, db: Session = Depends(get_db)):
    record = db.get(SiteSettings, 1, with_for_update=True)
    if any(
        getattr(data, key) != getattr(record, key)
        for key in ("boy_qq", "girl_qq")
        if key in data.model_fields_set
    ):
        invalidate_visitors(db)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    return {"message": "小站设置已保存"}


@app.patch("/api/admin/site", dependencies=[Depends(current_user)])
def update_site_section(changes: dict, db: Session = Depends(get_db)):
    record = db.get(SiteSettings, 1, with_for_update=True)
    current = {key: getattr(record, key) for key in SettingsInput.model_fields}
    try:
        validated = SettingsInput.model_validate({**current, **changes})
    except ValidationError as error:
        raise HTTPException(
            422, error.errors(include_context=False, include_input=False)
        ) from error
    if any(
        getattr(validated, key) != getattr(record, key) for key in ("boy_qq", "girl_qq")
    ):
        invalidate_visitors(db)
    for key in changes:
        setattr(record, key, getattr(validated, key))
    db.commit()
    return {"message": "设置已保存"}


@app.get("/api/admin/content/{kind}", dependencies=[Depends(current_user)])
def admin_content(
    kind: str,
    page: int = Query(1, ge=1, le=100000),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if kind not in PUBLIC_MODELS:
        raise HTTPException(404, "内容类型不存在")
    return page_result(db, PUBLIC_MODELS[kind], page, page_size)


def register_content(kind, model, schema):
    def create(data, db: Session = Depends(get_db)):
        record = model(**data.model_dump())
        db.add(record)
        db.commit()
        return serialize(record)

    def update(record_id: int, data, db: Session = Depends(get_db)):
        record = get_record(db, model, record_id)
        for key, value in data.model_dump().items():
            setattr(record, key, value)
        db.commit()
        return serialize(record)

    create.__annotations__["data"] = schema
    update.__annotations__["data"] = schema
    app.add_api_route(
        f"/api/admin/{kind}",
        create,
        methods=["POST"],
        status_code=201,
        dependencies=[Depends(current_user)],
        name=f"create_{kind}",
    )
    app.add_api_route(
        f"/api/admin/{kind}/{{record_id}}",
        update,
        methods=["PUT"],
        dependencies=[Depends(current_user)],
        name=f"update_{kind}",
    )


for kind, model, schema in [
    ("articles", Article, ArticleInput),
    ("photos", Photo, PhotoInput),
    ("wishes", Wish, WishInput),
    ("gifts", Gift, GiftInput),
]:
    register_content(kind, model, schema)


@app.delete(
    "/api/admin/{kind}/{record_id}",
    status_code=204,
    dependencies=[Depends(current_user)],
)
def delete_record(kind: str, record_id: int, db: Session = Depends(get_db)):
    if kind not in PUBLIC_MODELS:
        raise HTTPException(404, "内容类型不存在")
    db.delete(get_record(db, PUBLIC_MODELS[kind], record_id))
    db.commit()


@app.patch("/api/admin/messages/{record_id}", dependencies=[Depends(current_user)])
def moderate(record_id: int, data: ModerationInput, db: Session = Depends(get_db)):
    record = get_record(db, Message, record_id)
    record.approved = data.approved
    db.commit()
    return serialize(record)


@app.post("/api/admin/upload", dependencies=[Depends(current_user)], status_code=201)
async def upload(file: UploadFile = File(...)):
    data = await file.read(8 * 1024 * 1024 + 1)
    await file.close()
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(413, "图片不能超过 8MB")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as img:
                if (
                    img.format not in {"JPEG", "PNG", "WEBP"}
                    or img.width * img.height > 25000000
                ):
                    raise ValueError()
                img.load()
                result = ImageOps.exif_transpose(img).convert("RGB")
                result.thumbnail((2560, 2560))
                filename = f"{uuid4().hex}.webp"
                result.save(settings.upload_dir / filename, "WEBP", quality=88)
    except (
        UnidentifiedImageError,
        ValueError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise HTTPException(
            400, "请上传有效的 JPG、PNG 或 WebP 图片（不超过 2500 万像素）"
        ) from None
    return {"url": f"/uploads/{filename}"}
