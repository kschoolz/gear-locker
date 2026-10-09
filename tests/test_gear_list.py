import base64

import pytest


def create(client, n, category="other"):
    return [
        client.post("/gear", json={"name": f"Item {i}", "brand": "Acme", "category": category}).json()
        for i in range(n)
    ]


def ids(response):
    return [item["id"] for item in response.json()["items"]]


def test_empty_list(client):
    response = client.get("/gear")
    assert response.status_code == 200
    assert response.json() == {"items": [], "next_cursor": None}


def test_newest_first_and_full_items(client):
    items = create(client, 3)
    response = client.get("/gear")
    assert response.json() == {"items": items[::-1], "next_cursor": None}


def test_exactly_one_page_has_no_next_cursor(client):
    create(client, 20)
    response = client.get("/gear")
    assert len(response.json()["items"]) == 20
    assert response.json()["next_cursor"] is None


def test_cursor_walks_all_pages(client):
    items = create(client, 45)
    expected = [item["id"] for item in items[::-1]]
    first = client.get("/gear")
    second = client.get("/gear", params={"cursor": first.json()["next_cursor"]})
    third = client.get("/gear", params={"cursor": second.json()["next_cursor"]})
    assert ids(first) + ids(second) + ids(third) == expected
    assert [len(ids(r)) for r in (first, second, third)] == [20, 20, 5]
    assert third.json()["next_cursor"] is None


def test_retired_items_hidden(client):
    kept, retired = create(client, 2)
    client.post(f"/gear/{retired['id']}/retire")
    assert ids(client.get("/gear")) == [kept["id"]]


def test_category_filter_with_cursor(client):
    ropes = create(client, 22, category="rope")
    create(client, 3, category="sleep")
    first = client.get("/gear", params={"category": "rope"})
    second = client.get("/gear", params={"category": "rope", "cursor": first.json()["next_cursor"]})
    assert ids(first) + ids(second) == [item["id"] for item in ropes[::-1]]


@pytest.mark.parametrize("params", [{"category": "Rope"}, {"category": "soft goods"}])
def test_bad_category_is_422(client, params):
    response = client.get("/gear", params=params)
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


@pytest.mark.parametrize(
    "cursor",
    ["", "!!!", "abc", base64.urlsafe_b64encode(b"x1").decode(), base64.urlsafe_b64encode(b"0").decode()],
)
def test_malformed_cursor_is_422(client, cursor):
    response = client.get("/gear", params={"cursor": cursor})
    assert response.status_code == 422
    assert response.json() == {"error": "validation_error", "message": "cursor: invalid cursor"}
