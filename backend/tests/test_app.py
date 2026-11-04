from io import BytesIO

import pytest
from PIL import Image


def test_site_and_health(admin):
    client = admin
    assert client.get("/api/health").json() == {"status": "ok", "database": "sqlite"}
    site = client.get("/api/site").json()
    assert site["start_date"].endswith("+08:00")
    assert site["stats"]["articles"] == 2
    assert "password_hash" not in str(site)
    assert client.get("/api/openapi.json").status_code == 200


@pytest.mark.parametrize(
    "path,method",
    [
        ("/api/admin/content/articles", "get"),
        ("/api/admin/articles", "post"),
        ("/api/admin/articles/1", "put"),
        ("/api/admin/articles/1", "delete"),
        ("/api/admin/places/1", "put"),
        ("/api/admin/site", "put"),
        ("/api/admin/site", "patch"),
        ("/api/admin/upload", "post"),
    ],
)
def test_admin_routes_require_login(client, path, method):
    assert getattr(client, method)(path).status_code == 401


def test_login_cookie_logout_revokes_token(client):
    assert (
        client.post(
            "/api/auth/login", json={"username": "admin", "password": "wrong"}
        ).status_code
        == 401
    )
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "test-only-password-2026"},
    )
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie
    token = client.cookies.get("session")
    assert client.get("/api/auth/me").json()["username"] == "admin"
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.set("session", token)
    assert client.get("/api/auth/me").status_code == 401


def test_csrf_origin_check(admin):
    assert (
        admin.post(
            "/api/admin/wishes",
            json={"title": "blocked"},
            headers={"Origin": "https://evil.example"},
        ).status_code
        == 403
    )
    assert (
        admin.post(
            "/api/admin/wishes",
            json={"title": "allowed"},
            headers={"Origin": "http://localhost:5173"},
        ).status_code
        == 201
    )


@pytest.mark.parametrize(
    "kind,data",
    [
        (
            "articles",
            {
                "title": "new story",
                "content": "first line\nsecond line",
                "author": "test",
                "date": "2024-06-01",
            },
        ),
        (
            "photos",
            {
                "title": "new photo",
                "image": "/images/cover.png",
                "date": "2024-06-01",
                "location": "here",
            },
        ),
        (
            "wishes",
            {"title": "new wish", "completed": True, "date": "2024-06-01", "image": ""},
        ),
        ("places", {"title": "旅行", "city_id": "hangzhou", "date": "2025-06-01"}),
        (
            "anniversaries",
            {"title": "第一次见面", "date": "2024-02-29", "annual": True},
        ),
    ],
)
def test_content_round_trip_and_pagination(admin, kind, data):
    response = admin.post(f"/api/admin/{kind}", json=data)
    assert response.status_code == 201, response.text
    record = response.json()
    record_id = record["id"]
    public = admin.get(f"/api/content/{kind}?page_size=1").json()
    assert len(public["items"]) == 1 and public["items"][0]["id"] == record_id
    data["title"] = "updated"
    assert (
        admin.put(f"/api/admin/{kind}/{record_id}", json=data).json()["title"]
        == "updated"
    )
    assert admin.delete(f"/api/admin/{kind}/{record_id}").status_code == 204
    assert admin.put(f"/api/admin/{kind}/{record_id}", json=data).status_code == 404


def test_drafts_are_private(admin):
    result = admin.post(
        "/api/admin/articles",
        json={
            "title": "secret",
            "content": "private draft",
            "author": "me",
            "date": "2024-01-01",
            "published": False,
        },
    ).json()
    assert admin.get(f"/api/articles/{result['id']}").status_code == 404
    assert all(
        item["id"] != result["id"]
        for item in admin.get("/api/content/articles").json()["items"]
    )
    assert any(
        item["id"] == result["id"]
        for item in admin.get("/api/admin/content/articles").json()["items"]
    )


def test_retired_modules(admin):
    for kind in ("messages", "gifts"):
        assert admin.get(f"/api/content/{kind}").status_code == 404
        assert admin.get(f"/api/admin/content/{kind}").status_code == 404
    assert admin.post("/api/messages", json={}).status_code == 404


def site_payload(client):
    data = client.get("/api/site").json()
    for key in ["id", "source_url", "stats"]:
        data.pop(key)
    return data


def test_site_settings(admin):
    data = site_payload(admin)
    data.update(boy_name="测试", start_date="2024-05-19T16:00:00Z")
    assert admin.put("/api/admin/site", json=data).status_code == 200
    site = admin.get("/api/site").json()
    assert (
        site["boy_name"] == "测试" and site["start_date"] == "2024-05-20T00:00:00+08:00"
    )
    data["start_date"] = "2099-01-01T00:00:00"
    assert admin.put("/api/admin/site", json=data).status_code == 422


def test_password_change_invalidates_all_sessions(admin):
    old_token = admin.cookies.get("session")
    assert (
        admin.post(
            "/api/auth/password",
            json={"current_password": "bad", "new_password": "new-test-password-12345"},
        ).status_code
        == 400
    )
    assert (
        admin.post(
            "/api/auth/password",
            json={
                "current_password": "test-only-password-2026",
                "new_password": "new-test-password-12345",
            },
        ).status_code
        == 200
    )
    admin.cookies.set("session", old_token)
    assert admin.get("/api/auth/me").status_code == 401
    assert (
        admin.post(
            "/api/auth/login",
            json={"username": "admin", "password": "test-only-password-2026"},
        ).status_code
        == 401
    )
    assert (
        admin.post(
            "/api/auth/login",
            json={"username": "admin", "password": "new-test-password-12345"},
        ).status_code
        == 200
    )


def test_image_upload_reencoding(admin):
    image = Image.new("RGB", (20, 20), "pink")
    stream = BytesIO()
    image.save(stream, format="PNG")
    response = admin.post(
        "/api/admin/upload",
        files={"file": ("photo.png", stream.getvalue(), "image/png")},
    )
    assert response.status_code == 201
    url = response.json()["url"]
    assert url.startswith("/uploads/") and url.endswith(".webp")
    downloaded = admin.get(url)
    assert downloaded.status_code == 200
    assert Image.open(BytesIO(downloaded.content)).format == "WEBP"
    assert (
        admin.post(
            "/api/admin/upload",
            files={"file": ("bad.svg", b'<svg onload="alert(1)"/>', "image/svg+xml")},
        ).status_code
        == 400
    )
    assert (
        admin.post(
            "/api/admin/upload",
            files={"file": ("large.png", b"x" * (30 * 1024 * 1024 + 1), "image/png")},
        ).status_code
        == 413
    )


def test_image_upload_accepts_30mb_and_preserves_orientation(admin):
    image = Image.new("RGB", (40, 20), "pink")
    exif = Image.Exif()
    exif[274] = 6
    stream = BytesIO()
    image.save(stream, format="JPEG", exif=exif)
    data = stream.getvalue().ljust(30 * 1024 * 1024, b"\0")
    response = admin.post(
        "/api/admin/upload", files={"file": ("photo.jpg", data, "image/jpeg")}
    )
    assert response.status_code == 201
    uploaded = admin.get(response.json()["url"])
    assert uploaded.headers["content-type"] == "image/webp"
    result = Image.open(BytesIO(uploaded.content))
    assert result.size == (20, 40)
    assert not result.getexif()


def test_input_validation(admin):
    assert (
        admin.post(
            "/api/admin/places",
            json={"title": "Trip", "city_id": "unknown", "date": "2025-01-01"},
        ).status_code
        == 422
    )
    assert (
        admin.post(
            "/api/admin/photos",
            json={"title": "hi", "image": "javascript:alert(1)", "date": "2024-01-01"},
        ).status_code
        == 422
    )
    assert (
        admin.post(
            "/api/admin/photos",
            json={"title": "hi", "image": "/uploads/../../.env", "date": "2024-01-01"},
        ).status_code
        == 422
    )
    assert admin.get("/api/content/photos?page=0").status_code == 422
    assert admin.get("/api/content/unknown").status_code == 404


def test_rate_limits(admin):
    client = admin
    # The admin fixture already used one of the ten login attempts.
    for _ in range(9):
        assert (
            client.post(
                "/api/auth/login", json={"username": "wrong", "password": "wrong"}
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/api/auth/login", json={"username": "wrong", "password": "wrong"}
        ).status_code
        == 429
    )
