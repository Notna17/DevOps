"""
Post-deployment verification tests using testinfra and requests.
Verifies that the deployment is correct and the service is working.
Usage: pytest test_deployment.py --target-ip=<IP>
"""
import pytest
import requests


def pytest_addoption(parser):
    parser.addoption("--target-ip", action="store", required=True)


@pytest.fixture
def base_url(request):
    ip = request.config.getoption("--target-ip")
    return f"http://{ip}"


def test_root_endpoint_is_accessible(base_url):
    r = requests.get(f"{base_url}/", headers={"Accept": "text/html"}, timeout=10)
    assert r.status_code == 200
    assert "/items" in r.text


def test_items_endpoint_returns_json(base_url):
    r = requests.get(
        f"{base_url}/items",
        headers={"Accept": "application/json"},
        timeout=10,
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_items_endpoint_returns_html(base_url):
    r = requests.get(
        f"{base_url}/items",
        headers={"Accept": "text/html"},
        timeout=10,
    )
    assert r.status_code == 200
    assert "<table" in r.text.lower()


def test_create_and_retrieve_item(base_url):
    payload = {"name": "CI Test Item", "quantity": 42}
    create = requests.post(f"{base_url}/items", json=payload, timeout=10)
    assert create.status_code == 201
    item_id = create.json()["id"]

    get_item = requests.get(
        f"{base_url}/items/{item_id}",
        headers={"Accept": "application/json"},
        timeout=10,
    )
    assert get_item.status_code == 200
    assert get_item.json()["name"] == "CI Test Item"
    assert get_item.json()["quantity"] == 42


def test_health_alive_blocked_by_nginx(base_url):
    r = requests.get(f"{base_url}/health/alive", timeout=10)
    assert r.status_code == 404


def test_health_ready_blocked_by_nginx(base_url):
    r = requests.get(f"{base_url}/health/ready", timeout=10)
    assert r.status_code == 404


def test_nonexistent_path_blocked_by_nginx(base_url):
    r = requests.get(f"{base_url}/admin", timeout=10)
    assert r.status_code == 404

    r = requests.get(f"{base_url}/metrics", timeout=10)
    assert r.status_code == 404
