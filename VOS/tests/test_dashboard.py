"""Tests for dashboard_server.py — Flask API with auth."""
import sys
import os
import json
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


@pytest.fixture
def app():
    """Create a test Flask app with a temp database."""
    # Temporarily set DB_FILE to a temp file
    import dashboard_server
    original_db = dashboard_server.DB_FILE
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        dashboard_server.DB_FILE = f.name

    dashboard_server.app.config["TESTING"] = True
    yield dashboard_server.app

    # Cleanup
    dashboard_server.DB_FILE = original_db
    try:
        os.unlink(f.name)
    except Exception:
        pass


@pytest.fixture
def client(app):
    return app.test_client()


def _login(client):
    """Helper to log in for session-based auth."""
    return client.post("/login", data={"password": "sysprobe2024"},
                       follow_redirects=True)


def test_login_page_loads(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"password" in resp.data.lower()


def test_login_wrong_password(client):
    resp = client.post("/login", data={"password": "wrong"})
    assert resp.status_code == 200
    assert b"invalid" in resp.data.lower() or b"Invalid" in resp.data


def test_login_correct_password(client):
    resp = client.post("/login", data={"password": "sysprobe2024"},
                       follow_redirects=True)
    assert resp.status_code == 200


def test_dashboard_requires_login(client):
    resp = client.get("/")
    assert resp.status_code == 302  # redirect to login


def test_post_without_api_key(client):
    resp = client.post("/api/results",
                       data=json.dumps({"agent_name": "Test"}),
                       content_type="application/json")
    assert resp.status_code == 401


def test_post_with_api_key(client):
    resp = client.post("/api/results",
                       data=json.dumps({
                           "agent_name": "Test Agent",
                           "anydesk_id": "123456789",
                       }),
                       content_type="application/json",
                       headers={"X-API-Key": "sysprobe-default-key"})
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["status"] == "ok"


def test_get_results_requires_login(client):
    resp = client.get("/api/results")
    assert resp.status_code == 302


def test_get_results_after_login(client):
    _login(client)
    resp = client.get("/api/results")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert isinstance(data, list)


def test_post_then_get(client):
    # Post a result
    client.post("/api/results",
                data=json.dumps({"agent_name": "Alice", "mic_level": "95/100"}),
                content_type="application/json",
                headers={"X-API-Key": "sysprobe-default-key"})

    # Login and get
    _login(client)
    resp = client.get("/api/results")
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert any(r["agent_name"] == "Alice" for r in data)


def test_history_endpoint(client):
    # Post multiple results
    for i in range(3):
        client.post("/api/results",
                    data=json.dumps({"agent_name": "Bob", "mic_level": f"{90+i}/100"}),
                    content_type="application/json",
                    headers={"X-API-Key": "sysprobe-default-key"})

    _login(client)
    resp = client.get("/api/history/Bob")
    data = json.loads(resp.data)
    assert len(data) == 3
