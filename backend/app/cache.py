"""Short-lived, authenticated site-data cache. Redis failure falls back to SQL."""

import json
from uuid import uuid4

from redis import Redis, RedisError

from .config import settings

client = Redis.from_url(
    settings.redis_url, decode_responses=True,
    socket_connect_timeout=0.2, socket_timeout=0.2,
) if settings.redis_url else None


def site_key():
    if client is None:
        return None
    try:
        client.set("site:version", uuid4().hex, nx=True)
        return "site:data:" + client.get("site:version")
    except (RedisError, TypeError):
        return None


def read(key):
    if key is None:
        return None
    try:
        value = client.get(key)
        return json.loads(value) if value else None
    except (RedisError, ValueError):
        return None


def write(key, data):
    if key is None:
        return
    try:
        client.set(key, json.dumps(data), ex=30)
    except RedisError:
        pass


def invalidate():
    if client is None:
        return
    try:
        client.set("site:version", uuid4().hex)
    except RedisError:
        pass
