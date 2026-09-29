from fastapi.testclient import TestClient
import uuid
from main import app


client = TestClient(app)


def test_signup():
    email = f"testuser_{uuid.uuid4()}@example.com"

    response = client.post(
        "/api/auth/signup",
        json={
            "name": "Test User",
            "email": email,
            "password": "password123",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == email


def test_duplicate_signup():
    client.post(
        "/api/auth/signup",
        json={
            "name": "Test User",
            "email": "duplicate@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/api/auth/signup",
        json={
            "name": "Another User",
            "email": "duplicate@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 409


def test_login():
    client.post(
        "/api/auth/signup",
        json={
            "name": "Login User",
            "email": "login@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "login@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password():
    client.post(
        "/api/auth/signup",
        json={
            "name": "Wrong Password User",
            "email": "wrongpass@example.com",
            "password": "password123",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401


def test_me_without_token():
    response = client.get("/api/auth/me")

    assert response.status_code == 401