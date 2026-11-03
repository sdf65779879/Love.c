from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from threading import Lock
from time import monotonic

import jwt
from fastapi import Depends, HTTPException, Request
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User

password_hash = PasswordHash.recommended()
dummy_hash = password_hash.hash("timing-comparison-placeholder")


def token_for(user: User) -> str:
    return jwt.encode(
        {
            "sub": str(user.id),
            "v": user.token_version,
            "exp": datetime.now(UTC) + timedelta(hours=12),
        },
        settings.secret_key,
        algorithm="HS256",
    )


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(
            request.cookies.get("session", ""),
            settings.secret_key,
            algorithms=["HS256"],
            options={"require": ["sub", "exp", "v"]},
        )
        user = db.get(User, int(payload["sub"]))
        if not user or payload["v"] != user.token_version:
            raise ValueError()
        return user
    except (jwt.PyJWTError, ValueError, TypeError):
        raise HTTPException(401, "请先登录管理后台") from None


class RateLimiter:
    def __init__(self):
        self.buckets = defaultdict(deque)
        self.lock = Lock()

    def check(self, key: str, limit: int, window: int):
        now = monotonic()
        with self.lock:
            # Remove stale keys so anonymous traffic cannot grow memory indefinitely.
            for old_key in list(self.buckets):
                if not self.buckets[old_key] or now - self.buckets[old_key][-1] >= 3600:
                    del self.buckets[old_key]
            bucket = self.buckets[key]
            while bucket and now - bucket[0] >= window:
                bucket.popleft()
            if len(bucket) >= limit:
                raise HTTPException(
                    429, "操作太频繁，请稍后再试", headers={"Retry-After": str(window)}
                )
            bucket.append(now)


limiter = RateLimiter()
