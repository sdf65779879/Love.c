"""Exercise the running Nginx / FastAPI / MySQL stack with isolated records."""

import json
import os
import tarfile
from http.cookiejar import CookieJar
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]


def main():
    env = dict(
        line.split("=", 1)
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#") and "=" in line
    )
    origin = os.environ.get(
        "SMOKE_ORIGIN", f"http://localhost:{env.get('APP_PORT', '8080')}"
    )
    opener = build_opener(HTTPCookieProcessor(CookieJar()))
    created = []

    def request(path, method="GET", data=None, expected=200):
        body = json.dumps(data).encode() if data is not None else None
        req = Request(
            origin + path,
            data=body,
            method=method,
            headers={"Content-Type": "application/json", "Origin": origin},
        )
        try:
            with opener.open(req, timeout=20) as response:
                status, payload = response.status, response.read()
        except HTTPError as error:
            status, payload = error.code, error.read()
        assert status == expected, f"{method} {path}: expected {expected}, got {status}"
        return (
            json.loads(payload) if payload and payload[:1] in (b"{", b"[") else payload
        )

    tag = "smoke-" + uuid4().hex[:12]
    try:
        assert request("/api/health")["database"] == "mysql"
        for route in [
            "/",
            "/moments",
            "/album",
            "/wishlist",
            "/anniversaries",
            "/places",
            "/about",
            "/login",
            "/admin",
        ]:
            assert b'id="app"' in request(route)
        assert request("/api/openapi.json")["info"]["version"] == "1.0.0"
        request("/api/admin/content/articles", expected=401)
        for private_path in [
            "/api/site",
            "/api/content/photos",
            "/api/articles/1",
            "/source.tar.gz",
        ]:
            request(private_path, expected=401)
        request(
            "/api/auth/login",
            "POST",
            {
                "username": env.get("ADMIN_USERNAME", "admin"),
                "password": os.environ.get(
                    "SMOKE_ADMIN_PASSWORD", env["ADMIN_PASSWORD"]
                ),
            },
        )
        for kind, payload in [
            (
                "articles",
                {
                    "title": tag,
                    "content": "我们的故事🌷" * 7000,
                    "author": "smoke",
                    "date": "2024-05-20",
                    "published": False,
                },
            ),
            (
                "photos",
                {"title": tag, "image": "/images/cover.png", "date": "2024-05-20"},
            ),
            ("wishes", {"title": tag, "completed": False}),
            ("places", {"title": tag, "city_id": "hangzhou", "date": "2024-05-20"}),
            ("anniversaries", {"title": tag, "annual": True, "date": "2024-05-20"}),
        ]:
            record = request(f"/api/admin/{kind}", "POST", payload, 201)
            created.append((kind, record["id"]))
            payload["title"] = tag + "-updated"
            assert (
                request(f"/api/admin/{kind}/{record['id']}", "PUT", payload)["title"]
                == payload["title"]
            )
            if kind == "articles":
                request(f"/api/articles/{record['id']}", expected=404)
                payload["published"] = True
                request(f"/api/admin/{kind}/{record['id']}", "PUT", payload)
                assert (
                    request(f"/api/articles/{record['id']}")["content"]
                    == payload["content"]
                )
            assert any(
                item["id"] == record["id"]
                for item in request(f"/api/content/{kind}")["items"]
            )
        with tarfile.open(
            fileobj=BytesIO(request("/source.tar.gz")), mode="r:gz"
        ) as archive:
            names = archive.getnames()
            assert (
                "./backend/app/main.py" in names and "./frontend/src/App.vue" in names
            )
            assert not any(
                Path(name).name == ".env"
                or "/node_modules/" in name
                or "/.git/" in name
                for name in names
            )
        print(
            "PASS: MySQL health, 9 routes, auth, 5 CRUD flows, draft isolation, source archive"
        )
    finally:
        for kind, record_id in reversed(created):
            request(f"/api/admin/{kind}/{record_id}", "DELETE", expected=204)
        if created:
            request("/api/auth/logout", "POST")
            request("/api/auth/me", expected=401)
            print("PASS: test records removed; session revoked")


if __name__ == "__main__":
    main()
