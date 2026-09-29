import uuid

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def user_factory(client):
    def create_user(name="Test User"):
        email = f"{uuid.uuid4()}@example.com"
        password = "password123"
        signup_response = client.post("/api/auth/signup", json={"name": name, "email": email, "password": password})
        assert signup_response.status_code == 201
        login_response = client.post("/api/auth/login", json={"email": email, "password": password})
        assert login_response.status_code == 200
        return {"id": signup_response.json()["id"], "token": login_response.json()["access_token"]}

    return create_user


@pytest.fixture
def catalogue_factory(client, user_factory):
    def create_catalogue(price=500.0):
        user = user_factory("Catalogue User")
        headers = {"Authorization": f"Bearer {user['token']}"}
        suffix = uuid.uuid4()
        centre_response = client.post("/api/centres/", headers=headers, json={"name": f"Centre {suffix}", "location": "Test Location"})
        assert centre_response.status_code == 201
        test_response = client.post("/api/tests/", headers=headers, json={"name": f"Test {suffix}"})
        assert test_response.status_code == 201
        centre_id = centre_response.json()["id"]
        test_id = test_response.json()["id"]
        mapping_response = client.post(f"/api/centres/{centre_id}/tests/", headers=headers, json={"test_id": test_id, "price": price})
        assert mapping_response.status_code == 201
        return {"centre_id": centre_id, "test_id": test_id, "price": price}

    return create_catalogue
