import pytest
from fastapi.testclient import TestClient
from main import app
import main

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_invalid_private_ip():
    # 'testclient' is default in FastAPI TestClient, which fails IP parsing and caught as Private
    response = client.get("/")
    assert response.status_code == 400
    # The default text/html response will return plain text
    assert "Error: [INVALID_OR_PRIVATE_IP]" in response.text

    # Private IP directly via Header
    response = client.get("/", headers={"X-Appengine-User-Ip": "192.168.1.1"})
    assert response.status_code == 400

def test_valid_json_response():
    headers = {
        "X-Appengine-User-Ip": "8.8.8.8",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["ipv4"] == "8.8.8.8"
    assert data["os"] == "Windows 10"
    assert data["browser"] == "Chrome 91.0.4472"

def test_valid_plain_text_response():
    headers = {
        "X-Appengine-User-Ip": "8.8.8.8",
        "Accept": "text/html",
        "User-Agent": "python-requests/2.25.1"
    }
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    assert "ipv4: 8.8.8.8" in response.text
    # Requests usually parsed as generic, OS might be N/A
    assert "OS:" in response.text

def test_api_trace_always_json():
    # Even if accept is text/html, /api/v1/trace returns JSON
    headers = {
        "X-Appengine-User-Ip": "1.1.1.1",
        "Accept": "text/html"
    }
    response = client.get("/api/v1/trace", headers=headers)
    assert response.status_code == 200
    try:
        data = response.json()
        assert data["ipv4"] == "1.1.1.1"
    except Exception:
        pytest.fail("API trace did not return JSON")

def test_anonymize_ipv4():
    headers = {"X-Appengine-User-Ip": "8.8.4.4"}
    response = client.get("/api/v1/trace?anonymize=true", headers=headers)
    assert response.status_code == 200
    assert response.json()["ipv4"] == "8.8.4.0"

def test_anonymize_ipv6():
    headers = {"X-Appengine-User-Ip": "2001:4860:4860::8888"}
    response = client.get("/api/v1/trace?anonymize=true", headers=headers)
    assert response.status_code == 200
    assert response.json()["ipv6"] == "2001:4860:4860::"

def test_graceful_degradation(monkeypatch):
    # Mock get_geoip_data to return empty dict simulating an API failure
    async def mock_get_geoip_data(ip):
        return {}
    
    monkeypatch.setattr(main, "get_geoip_data", mock_get_geoip_data)

    headers = {
        "X-Appengine-User-Ip": "8.8.4.4",
        "Accept": "application/json"
    }
    response = client.get("/", headers=headers)
    assert response.status_code == 200
    # Must have the degradation header
    assert response.headers.get("X-Service-Warning") == "Partial Data"
    
    data = response.json()
    assert data["ipv4"] == "8.8.4.4"
    assert data["city"] is None
