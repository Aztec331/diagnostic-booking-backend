import uuid


def test_create_payment_without_token(client):
    response = client.post(
        "/api/payments/",
        json={
            "booking_id": 999999,
        },
    )

    assert response.status_code == 401


def test_create_payment_invalid_booking(client, user_factory):
    user = user_factory()

    response = client.post(
        "/api/payments/",
        headers={"Authorization": f"Bearer {user['token']}"},
        json={
            "booking_id": 999999,
        },
    )

    assert response.status_code == 404


def test_create_payment_for_another_users_booking(client, user_factory, catalogue_factory):
    user1 = user_factory("First User")
    user2 = user_factory("Second User")
    catalogue = catalogue_factory()

    booking_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {user2['token']}"},
        json={
            "centre_id": catalogue["centre_id"],
            "test_id": catalogue["test_id"],
            "appointment_at": f"2030-02-01T10:00:{uuid.uuid4().int % 60:02d}",
        },
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    response = client.post(
        "/api/payments/",
        headers={"Authorization": f"Bearer {user1['token']}"},
        json={
            "booking_id": booking_id,
        },
    )

    assert response.status_code == 404


def test_create_payment(client, user_factory, catalogue_factory):
    user = user_factory()
    catalogue = catalogue_factory(price=550.0)

    booking_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {user['token']}"},
        json={
            "centre_id": catalogue["centre_id"],
            "test_id": catalogue["test_id"],
            "appointment_at": f"2030-02-02T10:00:{uuid.uuid4().int % 60:02d}",
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
    assert response.json()["booking_id"] == booking_id
    assert response.json()["amount"] == 550.0
    assert response.json()["status"] == "PENDING"

def test_cannot_create_payment_for_cancelled_booking(client, user_factory, catalogue_factory):
    user = user_factory()
    catalogue = catalogue_factory()

    booking_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {user['token']}"},
        json={
            "centre_id": catalogue["centre_id"],
            "test_id": catalogue["test_id"],
            "appointment_at": f"2030-02-07T10:00:{uuid.uuid4().int % 60:02d}",
        },
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    cancel_response = client.patch(
        f"/api/bookings/{booking_id}/cancel",
        headers={"Authorization": f"Bearer {user['token']}"},
    )

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == "CANCELLED"

    payment_response = client.post(
        "/api/payments/",
        headers={"Authorization": f"Bearer {user['token']}"},
        json={
            "booking_id": booking_id,
        },
    )

    assert payment_response.status_code == 409
    assert payment_response.json()["detail"] == "Only pending bookings can be paid"


def test_duplicate_payment(client, user_factory, catalogue_factory):
    user = user_factory()
    catalogue = catalogue_factory()

    booking_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {user['token']}"},
        json={
            "centre_id": catalogue["centre_id"],
            "test_id": catalogue["test_id"],
            "appointment_at": f"2030-02-03T10:00:{uuid.uuid4().int % 60:02d}",
        },
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    first_response = client.post(
        "/api/payments/",
        headers={"Authorization": f"Bearer {user['token']}"},
        json={
            "booking_id": booking_id,
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/payments/",
        headers={"Authorization": f"Bearer {user['token']}"},
        json={
            "booking_id": booking_id,
        },
    )

    assert second_response.status_code == 409


def test_webhook_invalid_payment(client):
    response = client.post(
        "/api/payments/webhook/",
        json={
            "event_id": f"invalid-payment-{uuid.uuid4()}",
            "payment_id": 999999,
            "event_type": "SUCCESS",
        },
    )

    assert response.status_code == 404


def test_webhook_invalid_event_type(client, user_factory, catalogue_factory):
    user = user_factory()
    catalogue = catalogue_factory()

    booking_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {user['token']}"},
        json={
            "centre_id": catalogue["centre_id"],
            "test_id": catalogue["test_id"],
            "appointment_at": f"2030-02-04T10:00:{uuid.uuid4().int % 60:02d}",
        },
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    payment_response = client.post(
        "/api/payments/",
        headers={"Authorization": f"Bearer {user['token']}"},
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


def test_success_webhook(client, user_factory, catalogue_factory):
    user = user_factory()
    catalogue = catalogue_factory()

    booking_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {user['token']}"},
        json={
            "centre_id": catalogue["centre_id"],
            "test_id": catalogue["test_id"],
            "appointment_at": f"2030-02-05T10:00:{uuid.uuid4().int % 60:02d}",
        },
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    payment_response = client.post(
        "/api/payments/",
        headers={"Authorization": f"Bearer {user['token']}"},
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


def test_duplicate_webhook_event(client, user_factory, catalogue_factory):
    user = user_factory()
    catalogue = catalogue_factory()

    booking_response = client.post(
        "/api/bookings/",
        headers={"Authorization": f"Bearer {user['token']}"},
        json={
            "centre_id": catalogue["centre_id"],
            "test_id": catalogue["test_id"],
            "appointment_at": f"2030-02-06T10:00:{uuid.uuid4().int % 60:02d}",
        },
    )

    assert booking_response.status_code == 201

    booking_id = booking_response.json()["id"]

    payment_response = client.post(
        "/api/payments/",
        headers={"Authorization": f"Bearer {user['token']}"},
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
