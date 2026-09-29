def test_webhook_missing_event_id(client):
    response = client.post(
        "/api/payments/webhook/",
        json={
            "payment_id": 3,
            "event_type": "SUCCESS",
        },
    )

    assert response.status_code == 422


def test_webhook_empty_event_id(client):
    response = client.post(
        "/api/payments/webhook/",
        json={
            "event_id": "",
            "payment_id": 3,
            "event_type": "SUCCESS",
        },
    )

    assert response.status_code == 422


def test_webhook_missing_payment_id(client):
    response = client.post(
        "/api/payments/webhook/",
        json={
            "event_id": "missing-payment-id",
            "event_type": "SUCCESS",
        },
    )

    assert response.status_code == 422
