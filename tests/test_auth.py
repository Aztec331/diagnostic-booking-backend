import uuid


def test_signup(client):
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


def test_duplicate_signup(client):
    email = f"duplicate_{uuid.uuid4()}@example.com"
    client.post(
        "/api/auth/signup",
        json={
            "name": "Test User",
            "email": email,
            "password": "password123",
        },
    )

    response = client.post(
        "/api/auth/signup",
        json={
            "name": "Another User",
            "email": email,
            "password": "password123",
        },
    )

    assert response.status_code == 409


def test_login(client):
    email = f"login_{uuid.uuid4()}@example.com"
    client.post(
        "/api/auth/signup",
        json={
            "name": "Login User",
            "email": email,
            "password": "password123",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password(client):
    email = f"wrongpass_{uuid.uuid4()}@example.com"
    client.post(
        "/api/auth/signup",
        json={
            "name": "Wrong Password User",
            "email": email,
            "password": "password123",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401


def test_me_without_token(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401
