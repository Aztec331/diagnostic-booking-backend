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


def test_create_payment_without_token():
    response = client.post(
        "/api/payments/",
        json={
            "booking_id": 999999,
        },
    )

    assert response.status_code == 401


def test_create_payment_invalid_booking():
    token = get_token("aditya@test.com", "password123")

    response = client.post(
        "/api/payments/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "booking_id": 999999,
        },
    )

    assert response.status_code == 404


def test_create_payment_for_another_users_booking():
    user1_token = get_token("aditya@test.com", "password123")
    user2_token = get_token("rahul@example.com", "password123")

    booking_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {user2_token}"},
        json={
            "centre_id": 5,
            "test_id": 5,
            "appointment_at": f"2030-02-01T10:00:{uuid.uuid4().int % 60:02d}",
        },
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    response = client.post(
        "/api/payments/",
        headers={"Authorization": f"Bearer {user1_token}"},
        json={
            "booking_id": booking_id,
        },
    )

    assert response.status_code == 404


def test_create_payment():
    token = get_token("aditya@test.com", "password123")

    booking_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "centre_id": 6,
            "test_id": 6,
            "appointment_at": f"2030-02-02T10:00:{uuid.uuid4().int % 60:02d}",
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
    assert response.json()["booking_id"] == booking_id
    assert response.json()["amount"] == 550.0
    assert response.json()["status"] == "PENDING"


def test_duplicate_payment():
    token = get_token("aditya@test.com", "password123")

    booking_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "centre_id": 1,
            "test_id": 1,
            "appointment_at": f"2030-02-03T10:00:{uuid.uuid4().int % 60:02d}",
        },
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    first_response = client.post(
        "/api/payments/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "booking_id": booking_id,
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/payments/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "booking_id": booking_id,
        },
    )

    assert second_response.status_code == 409


def test_webhook_invalid_payment():
    response = client.post(
        "/api/payments/webhook/",
        json={
            "event_id": f"invalid-payment-{uuid.uuid4()}",
            "payment_id": 999999,
            "event_type": "SUCCESS",
        },
    )

    assert response.status_code == 404


def test_webhook_invalid_event_type():
    token = get_token("aditya@test.com", "password123")

    booking_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "centre_id": 2,
            "test_id": 2,
            "appointment_at": f"2030-02-04T10:00:{uuid.uuid4().int % 60:02d}",
        },
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    payment_response = client.post(
        "/api/payments/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "booking_id": booking_id,
        },
    )

    assert payment_response.status_code == 201

    payment_id = payment_response.json()["id"]

    response = client.post(
        "/api/payments/webhook/",
        json={
            "event_id": f"invalid-event-{uuid.uuid4()}",
            "payment_id": payment_id,
            "event_type": "INVALID",
        },
    )

    assert response.status_code == 400


def test_success_webhook():
    token = get_token("aditya@test.com", "password123")

    booking_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "centre_id": 3,
            "test_id": 3,
            "appointment_at": f"2030-02-05T10:00:{uuid.uuid4().int % 60:02d}",
        },
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    payment_response = client.post(
        "/api/payments/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "booking_id": booking_id,
        },
    )

    assert payment_response.status_code == 201

    payment_id = payment_response.json()["id"]

    response = client.post(
        "/api/payments/webhook/",
        json={
            "event_id": f"success-event-{uuid.uuid4()}",
            "payment_id": payment_id,
            "event_type": "SUCCESS",
        },
    )

    assert response.status_code == 200
    assert response.json()["payment_status"] == "SUCCESS"
    assert response.json()["booking_status"] == "CONFIRMED"


def test_duplicate_webhook_event():
    token = get_token("aditya@test.com", "password123")

    booking_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "centre_id": 4,
            "test_id": 4,
            "appointment_at": f"2030-02-06T10:00:{uuid.uuid4().int % 60:02d}",
        },
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    payment_response = client.post(
        "/api/payments/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "booking_id": booking_id,
        },
    )

    assert payment_response.status_code == 201

    payment_id = payment_response.json()["id"]

    event_id = f"duplicate-event-{uuid.uuid4()}"

    first_response = client.post(
        "/api/payments/webhook/",
        json={
            "event_id": event_id,
            "payment_id": payment_id,
            "event_type": "SUCCESS",
        },
    )

    assert first_response.status_code == 200
    assert first_response.json()["payment_status"] == "SUCCESS"
    assert first_response.json()["booking_status"] == "CONFIRMED"

    second_response = client.post(
        "/api/payments/webhook/",
        json={
            "event_id": event_id,
            "payment_id": payment_id,
            "event_type": "SUCCESS",
        },
    )

    assert second_response.status_code == 200
    assert second_response.json()["message"] == "Event already processed"