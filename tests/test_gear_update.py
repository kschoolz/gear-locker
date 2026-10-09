from datetime import datetime, timedelta, timezone

import pytest

TOMORROW = (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat()


@pytest.fixture
def item(client):
    return client.post(
        "/gear",
        json={"name": "Tent", "brand": "MSR", "category": "shelter", "bought_date": "2023-04-01", "notes": "2p"},
    ).json()


def test_patch_updates_only_sent_fields(client, item):
    response = client.patch(f"/gear/{item['id']}", json={"name": "  Hubba Hubba  "})
    assert response.status_code == 200
    assert response.json() == {**item, "name": "Hubba Hubba"}


def test_patch_null_clears_optional_fields(client, item):
    response = client.patch(f"/gear/{item['id']}", json={"bought_date": None, "notes": None})
    assert response.status_code == 200
    assert response.json() == {**item, "bought_date": None, "notes": None}


def test_patch_blank_notes_clears_notes(client, item):
    response = client.patch(f"/gear/{item['id']}", json={"notes": "   "})
    assert response.json()["notes"] is None


def test_patch_unknown_id_is_404(client):
    response = client.patch("/gear/999", json={"name": "x"})
    assert response.status_code == 404
    assert response.json() == {"error": "not_found", "message": "item 999 not found"}


@pytest.mark.parametrize(
    "payload, message",
    [
        ({}, "at least one field is required"),
        ({"name": None}, "name: must not be null"),
        ({"brand": None}, "brand: must not be null"),
        ({"category": None}, "category: must not be null"),
        ({"name": "  "}, "name: must not be blank"),
        ({"bought_date": TOMORROW}, "bought_date: must not be in the future"),
        ({"category": "Rope"}, None),
        ({"color": "red"}, "color: Extra inputs are not permitted"),
        ({"id": 7}, "id: Extra inputs are not permitted"),
        ({"created_at": "2024-01-01T00:00:00Z"}, "created_at: Extra inputs are not permitted"),
        ({"retired_at": "2024-01-01T00:00:00Z"}, "retired_at: Extra inputs are not permitted"),
    ],
)
def test_patch_rejects_bad_input(client, item, payload, message):
    response = client.patch(f"/gear/{item['id']}", json=payload)
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"
    if message:
        assert response.json()["message"] == message
    assert client.get(f"/gear/{item['id']}").json() == item


def test_patch_non_integer_id_is_422(client):
    response = client.patch("/gear/abc", json={"name": "x"})
    assert response.status_code == 422
