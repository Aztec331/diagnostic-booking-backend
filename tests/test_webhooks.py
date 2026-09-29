from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_webhook_missing_event_id():
    response = client.post(
        "/api/payments/webhook/",
        json={
            "payment_id": 3,
            "event_type": "SUCCESS",
        },
    )

    assert response.status_code == 422


def test_webhook_empty_event_id():
    response = client.post(
        "/api/payments/webhook/",
        json={
            "event_id": "",
            "payment_id": 3,
            "event_type": "SUCCESS",
        },
    )

    assert response.status_code == 422


def test_webhook_missing_payment_id():
    response = client.post(
        "/api/payments/webhook/",
        json={
            "event_id": "missing-payment-id",
            "event_type": "SUCCESS",
        },
    )

    assert response.status_code == 422