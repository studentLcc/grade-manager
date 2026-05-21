from datetime import timedelta

from app.core.security import create_access_token, decode_access_token


def test_register_login_and_me(client):
    register = client.post(
        "/api/v1/auth/register",
        json={
            "username": "teacher1",
            "password": "strong-password",
            "display_name": "王老师",
            "email": "teacher1@example.com",
            "phone": "13800000000",
        },
    )
    assert register.status_code == 201
    assert register.json()["username"] == "teacher1"
    assert "password_hash" not in register.json()

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "teacher1", "password": "strong-password"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["display_name"] == "王老师"


def test_duplicate_username_returns_409(client):
    payload = {"username": "teacher1", "password": "strong-password", "display_name": "王老师"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["code"] == "DUPLICATE_RESOURCE"


def test_expired_token_is_rejected(client):
    token = create_access_token(subject="1", expires_delta=timedelta(seconds=-1))
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


def test_token_contains_teacher_id():
    token = create_access_token(subject="42", expires_delta=timedelta(days=30))
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert "exp" in payload
