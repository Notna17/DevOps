import pytest

from app import create_app


@pytest.fixture
def app():
    test_app = create_app(testing=True)
    yield test_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def client_no_db():
    test_app = create_app(testing=True)
    conn = test_app.config["DB_CONN"]
    conn.close()
    return test_app.test_client()


def test_alive_returns_200(client):
    response = client.get("/health/alive")
    assert response.status_code == 200
    assert response.data == b"OK"


def test_ready_returns_500_when_db_unavailable(client_no_db):
    response = client_no_db.get("/health/ready")
    assert response.status_code == 500


def test_get_items_empty(client):
    response = client.get("/items", headers={"Accept": "application/json"})
    assert response.status_code == 200
    assert response.json == []


def test_post_item_creates_record(client):
    response = client.post(
        "/items",
        json={"name": "Laptop", "quantity": 3},
        headers={"Accept": "application/json"},
    )
    assert response.status_code == 201
    assert response.json["name"] == "Laptop"


def test_get_item_by_id(client):
    create = client.post(
        "/items",
        json={"name": "Phone", "quantity": 2},
        headers={"Accept": "application/json"},
    )
    assert create.status_code == 201
    item_id = create.json["id"]

    response = client.get(f"/items/{item_id}", headers={"Accept": "application/json"})
    assert response.status_code == 200
    assert response.json["name"] == "Phone"
    assert response.json["quantity"] == 2


def test_get_items_html(client):
    response = client.get("/items", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert b"<table" in response.data


def test_get_nonexistent_item_returns_404(client):
    response = client.get("/items/99999", headers={"Accept": "application/json"})
    assert response.status_code == 404


def test_root_returns_html(client):
    response = client.get("/", headers={"Accept": "text/html"})
    assert response.status_code == 200
    assert b"/items" in response.data
