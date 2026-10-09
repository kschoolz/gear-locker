import pytest
from fastapi.testclient import TestClient

from app.db import get_connection, migrate
from app.main import app, get_db


@pytest.fixture
def client(tmp_path):
    db_path = tmp_path / "gear.db"
    migrate(db_path)

    def override_get_db():
        conn = get_connection(db_path)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
