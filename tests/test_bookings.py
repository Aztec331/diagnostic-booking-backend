from fastapi.testclient import TestClient

import uuid

from main import app


client = TestClient(app)


def get_token(email, password):
    response = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    return response.json()["access_token"]


def test_create_booking_without_token():
    response = client.post(
        "/api/bookings/",
        json={
            "centre_id": 1,
            "test_id": 1,
            "appointment_at": "2030-01-10T10:00:00",
        },
    )

    assert response.status_code == 401


def test_create_booking_invalid_centre_test():
    token = get_token("aditya@test.com", "password123")

    response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "centre_id": 999,
            "test_id": 999,
            "appointment_at": "2030-01-10T10:00:00",
        },
    )

    assert response.status_code == 404


def test_create_booking():
    token = get_token("aditya@test.com", "password123")

    response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "centre_id": 2,
            "test_id": 2,
            "appointment_at": f"2030-01-01T11:00:{uuid.uuid4().int % 60:02d}",
        },
    )

    assert response.status_code == 201
    assert response.json()["user_id"] == 1
    assert response.json()["centre_id"] == 2
    assert response.json()["test_id"] == 2
    assert response.json()["amount"] == 800.0
    assert response.json()["status"] == "PENDING"


def test_duplicate_booking():
    token = get_token("aditya@test.com", "password123")

    booking = {
        "centre_id": 3,
        "test_id": 3,
        "appointment_at": f"2030-01-02T10:00:{uuid.uuid4().int % 60:02d}",
    }

    first_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {token}"},
        json=booking,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {token}"},
        json=booking,
    )

    assert second_response.status_code == 409


def test_get_booking_of_another_user():
    user1_token = get_token("aditya@test.com", "password123")
    user2_token = get_token("rahul@example.com", "password123")

    booking_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {user2_token}"},
        json={
            "centre_id": 4,
            "test_id": 4,
            "appointment_at": f"2030-01-03T10:00:{uuid.uuid4().int % 60:02d}",
        },
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    response = client.get(
        f"/api/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {user1_token}"},
    )

    assert response.status_code == 404


def test_cancel_failed_booking():
    token = get_token("aditya@test.com", "password123")

    booking_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "centre_id": 5,
            "test_id": 5,
            "appointment_at": f"2030-01-04T10:00:{uuid.uuid4().int % 60:02d}",
        },
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    response = client.post(
        "/api/payments/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "booking_id": booking_id,
        },
    )

    assert response.status_code == 201

    payment_id = response.json()["id"]

    webhook_response = client.post(
        "/api/payments/webhook/",
        json={
            "event_id": f"failed-cancel-test-{uuid.uuid4()}",
            "payment_id": payment_id,
            "event_type": "FAILED",
        },
    )

    assert webhook_response.status_code == 200

    response = client.patch(
        f"/api/bookings/{booking_id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409


def test_cancel_without_token():
    response = client.patch("/api/bookings/999999/cancel")

    assert response.status_code == 401