import uuid


def test_create_booking_without_token(client):
    response = client.post(
        "/api/bookings/",
        json={
            "centre_id": 999999,
            "test_id": 999999,
            "appointment_at": "2030-01-10T10:00:00",
        },
    )

    assert response.status_code == 401


def test_create_booking_invalid_centre_test(client, user_factory):
    user = user_factory()

    response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {user['token']}"},
        json={
            "centre_id": 999,
            "test_id": 999,
            "appointment_at": "2030-01-10T10:00:00",
        },
    )

    assert response.status_code == 404


def test_create_booking(client, user_factory, catalogue_factory):
    user = user_factory()
    catalogue = catalogue_factory(price=800.0)

    response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {user['token']}"},
        json={
            "centre_id": catalogue["centre_id"],
            "test_id": catalogue["test_id"],
            "appointment_at": f"2030-01-01T11:00:{uuid.uuid4().int % 60:02d}",
        },
    )

    assert response.status_code == 201
    assert response.json()["user_id"] == user["id"]
    assert response.json()["centre_id"] == catalogue["centre_id"]
    assert response.json()["test_id"] == catalogue["test_id"]
    assert response.json()["amount"] == 800.0
    assert response.json()["status"] == "PENDING"


def test_duplicate_booking(client, user_factory, catalogue_factory):
    user = user_factory()
    catalogue = catalogue_factory()

    booking = {
        "centre_id": catalogue["centre_id"],
        "test_id": catalogue["test_id"],
        "appointment_at": f"2030-01-02T10:00:{uuid.uuid4().int % 60:02d}",
    }

    first_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {user['token']}"},
        json=booking,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {user['token']}"},
        json=booking,
    )

    assert second_response.status_code == 409


def test_get_booking_of_another_user(client, user_factory, catalogue_factory):
    user1 = user_factory("First User")
    user2 = user_factory("Second User")
    catalogue = catalogue_factory()

    booking_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {user2['token']}"},
        json={
            "centre_id": catalogue["centre_id"],
            "test_id": catalogue["test_id"],
            "appointment_at": f"2030-01-03T10:00:{uuid.uuid4().int % 60:02d}",
        },
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    response = client.get(
        f"/api/bookings/{booking_id}",
        headers={"Authorization": f"Bearer {user1['token']}"},
    )

    assert response.status_code == 404


def test_cancel_failed_booking(client, user_factory, catalogue_factory):
    user = user_factory()
    catalogue = catalogue_factory()

    booking_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {user['token']}"},
        json={
            "centre_id": catalogue["centre_id"],
            "test_id": catalogue["test_id"],
            "appointment_at": f"2030-01-04T10:00:{uuid.uuid4().int % 60:02d}",
        },
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    response = client.post(
        "/api/payments/",
        headers={"Authorization": f"Bearer {user['token']}"},
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
        headers={"Authorization": f"Bearer {user['token']}"},
    )

    assert response.status_code == 409


def test_cancel_without_token(client):
    response = client.patch("/api/bookings/999999/cancel")

    assert response.status_code == 401
