def test_get_returns_item(client):
    created = client.post("/gear", json={"name": "Cam #2", "brand": "Black Diamond", "category": "protection"}).json()
    response = client.get(f"/gear/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_get_unknown_id_is_404(client):
    response = client.get("/gear/999")
    assert response.status_code == 404
    assert response.json() == {"error": "not_found", "message": "item 999 not found"}


def test_get_non_integer_id_is_422(client):
    response = client.get("/gear/abc")
    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"
