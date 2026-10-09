import re
from datetime import datetime, timedelta, timezone

import pytest

VALID = {"name": "Dynamic rope 9.5", "brand": "Mammut", "category": "rope"}


def test_create_returns_201_and_full_item(client):
    response = client.post(
        "/gear",
        json={**VALID, "name": "  Dynamic rope 9.5  ", "bought_date": "2024-05-01", "notes": " 60m "},
    )
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["id"], int)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", body["created_at"])
    assert body == {
        "id": body["id"],
        "name": "Dynamic rope 9.5",
        "brand": "Mammut",
        "category": "rope",
        "bought_date": "2024-05-01",
        "notes": "60m",
        "retired_at": None,
        "created_at": body["created_at"],
    }


def test_create_null_optionals_and_blank_notes_become_null(client):
    response = client.post("/gear", json={**VALID, "bought_date": None, "notes": "   "})
    assert response.status_code == 201
    assert response.json()["bought_date"] is None
    assert response.json()["notes"] is None


TOMORROW = (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat()


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"brand": "Mammut", "category": "rope"}, id="missing_name"),
        pytest.param({**VALID, "name": ""}, id="empty_name"),
        pytest.param({**VALID, "name": "   "}, id="blank_name"),
        pytest.param({**VALID, "brand": ""}, id="empty_brand"),
        pytest.param({**VALID, "name": None}, id="null_name"),
        pytest.param({**VALID, "category": "Rope"}, id="category_wrong_case"),
        pytest.param({**VALID, "category": "soft goods"}, id="category_display_name"),
        pytest.param({**VALID, "bought_date": TOMORROW}, id="future_date"),
        pytest.param({**VALID, "bought_date": "2024/05/01"}, id="date_slashes"),
        pytest.param({**VALID, "bought_date": "20240501"}, id="date_no_dashes"),
        pytest.param({**VALID, "color": "red"}, id="unknown_field"),
        pytest.param({**VALID, "id": 5}, id="readonly_id"),
        pytest.param({**VALID, "created_at": "2024-01-01T00:00:00Z"}, id="readonly_created_at"),
        pytest.param({**VALID, "retired_at": "2024-01-01T00:00:00Z"}, id="readonly_retired_at"),
    ],
)
def test_create_rejects_bad_input(client, payload):
    response = client.post("/gear", json=payload)
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"
    assert response.json()["message"]


def test_create_error_messages(client):
    blank = client.post("/gear", json={**VALID, "name": "   "})
    assert blank.json()["message"] == "name: must not be blank"
    future = client.post("/gear", json={**VALID, "bought_date": TOMORROW})
    assert future.json()["message"] == "bought_date: must not be in the future"
