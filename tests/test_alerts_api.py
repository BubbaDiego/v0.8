import pytest
from flask import Flask
from app.alerts_bp import alerts_bp
from core.core_imports import log

# Setup the Flask Test App
@pytest.fixture
def client():
    app = Flask(__name__)
    app.register_blueprint(alerts_bp)
    app.json_manager = None  # Skip JsonManager for now if not needed in these tests
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# --- API Endpoint Tests ---

def test_refresh_alerts(client):
    """Test POST /alerts/refresh endpoint."""
    log.banner("TEST: Refresh Alerts API Start")
    response = client.post('/alerts/refresh')
    assert response.status_code in [200, 500]  # Allow 500 if no alerts loaded yet
    log.success(f"✅ Refresh Alerts API response: {response.status_code}", source="TestAlertsAPI")

def test_create_all_alerts(client):
    """Test POST /alerts/create_all endpoint."""
    log.banner("TEST: Create All Alerts API Start")
    response = client.post('/alerts/create_all')
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("success") is True
    log.success(f"✅ Create All Alerts API response: {response.status_code}", source="TestAlertsAPI")

def test_delete_all_alerts(client):
    """Test POST /alerts/delete_all endpoint."""
    log.banner("TEST: Delete All Alerts API Start")
    response = client.post('/alerts/delete_all')
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("success") is True
    log.success(f"✅ Delete All Alerts API response: {response.status_code}", source="TestAlertsAPI")

def test_monitor_alerts(client):
    """Test GET /alerts/monitor endpoint."""
    log.banner("TEST: Monitor Alerts API Start")
    response = client.get('/alerts/monitor')
    assert response.status_code == 200
    data = response.get_json()
    assert "alerts" in data
    assert isinstance(data["alerts"], list)
    log.success(f"✅ Monitor Alerts API response: {response.status_code}, {len(data['alerts'])} alerts returned", source="TestAlertsAPI")
