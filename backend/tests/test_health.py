def test_health_endpoint_success(client):
    """Test GET /health returns expected status and database connectivity."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "shiftguard-edge"
    assert data["database"] == "connected"


def test_root_endpoint(client):
    """Test GET / returns service metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "shiftguard-edge"
    assert data["status"] == "operational"
    assert "version" in data
