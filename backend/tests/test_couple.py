import pytest


def test_couple_profile_round_trip(admin):
    original = admin.get("/api/site").json()
    data = {"boy_qq": "12345678", "girl_qq": "987654321", "boy_name": "测试昵称"}
    assert admin.patch("/api/admin/site", json=data).status_code == 200
    updated = admin.get("/api/site").json()
    assert all(updated[key] == value for key, value in data.items())
    assert updated["girl_name"] == original["girl_name"]
    assert updated["boy_avatar"] == original["boy_avatar"]
    assert admin.patch("/api/admin/site", json={"title": "LOVE.C"}).status_code == 200
    assert admin.get("/api/site").json()["boy_qq"] == data["boy_qq"]
    assert (
        admin.patch("/api/admin/site", json={"boy_qq": "", "girl_qq": ""}).status_code
        == 200
    )
    cleared = admin.get("/api/site").json()
    assert cleared["boy_qq"] == cleared["girl_qq"] == ""
    assert cleared["boy_avatar"] == original["boy_avatar"]


@pytest.mark.parametrize(
    "qq", ["1234", "012345", "123456789012", "hello", "12345&x=1", None, 123456]
)
def test_invalid_qq_is_rejected_atomically(admin, qq):
    original = admin.get("/api/site").json()
    response = admin.patch(
        "/api/admin/site", json={"boy_qq": qq, "girl_name": "不要保存"}
    )
    assert response.status_code == 422
    current = admin.get("/api/site").json()
    assert current["boy_qq"] == original["boy_qq"]
    assert current["girl_name"] == original["girl_name"]


def test_qq_whitespace_and_unknown_settings(admin):
    assert (
        admin.patch("/api/admin/site", json={"girl_qq": " 123456 "}).status_code == 200
    )
    assert admin.get("/api/site").json()["girl_qq"] == "123456"
    assert (
        admin.patch("/api/admin/site", json={"unknown_field": "x"}).status_code == 422
    )
