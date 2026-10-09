import re

import pytest

from app.main import app, get_db


@pytest.fixture
def item(client):
    return client.post("/gear", json={"name": "Stove", "brand": "Jetboil", "category": "cooking"}).json()


def test_retire_sets_retired_at(client, item):
    response = client.post(f"/gear/{item['id']}/retire")
    assert response.status_code == 200
    body = response.json()
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", body["retired_at"])
    assert body == {**item, "retired_at": body["retired_at"]}


def test_retire_twice_returns_same_response(client, item):
    first = client.post(f"/gear/{item['id']}/retire")
    second = client.post(f"/gear/{item['id']}/retire")
    assert first.status_code == second.status_code == 200
    assert second.json() == first.json()


def test_retire_again_keeps_original_retired_at(client, item):
    client.post(f"/gear/{item['id']}/retire")
    db = app.dependency_overrides[get_db]()
    conn = next(db)
    conn.execute("UPDATE item SET retired_at = '2020-01-01T00:00:00Z' WHERE id = ?", (item["id"],))
    conn.commit()
    db.close()
    response = client.post(f"/gear/{item['id']}/retire")
    assert response.status_code == 200
    assert response.json()["retired_at"] == "2020-01-01T00:00:00Z"


def test_retired_item_can_be_fetched_and_patched(client, item):
    retired = client.post(f"/gear/{item['id']}/retire").json()
    assert client.get(f"/gear/{item['id']}").json() == retired
    response = client.patch(f"/gear/{item['id']}", json={"notes": "sold"})
    assert response.status_code == 200
    assert response.json() == {**retired, "notes": "sold"}


def test_retire_unknown_id_is_404(client):
    response = client.post("/gear/999/retire")
    assert response.status_code == 404
    assert response.json() == {"error": "not_found", "message": "item 999 not found"}


def test_retire_non_integer_id_is_422(client):
    response = client.post("/gear/abc/retire")
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"
