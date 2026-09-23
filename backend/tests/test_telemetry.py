def test_get_latest_telemetry_fleet(client, seed_test_data):
    """Test GET /api/telemetry/latest returns list of latest records for all machines."""
    response = client.get("/api/telemetry/latest")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2  # CAT-797F-101 and CAT-6060-201
    machine_ids = [d["machine_id"] for d in data]
    assert "CAT-797F-101" in machine_ids
    assert "CAT-6060-201" in machine_ids


def test_get_latest_telemetry_single_machine(client, seed_test_data):
    """Test GET /api/telemetry/latest with machine_id filter returns single record."""
    response = client.get("/api/telemetry/latest?machine_id=CAT-797F-101")
    assert response.status_code == 200
    data = response.json()
    assert data["machine_id"] == "CAT-797F-101"
    # Should be the later timestamp (06:01:00Z)
    assert data["timestamp"] == "2026-09-20T06:01:00Z"
    assert data["machine_speed_kmh"] == 32.0


def test_get_latest_telemetry_not_found(client, seed_test_data):
    """Test GET /api/telemetry/latest for non-existent machine returns 404."""
    response = client.get("/api/telemetry/latest?machine_id=CAT-DOES-NOT-EXIST")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_get_telemetry_history_all(client, seed_test_data):
    """Test GET /api/telemetry returns all seeded records."""
    response = client.get("/api/telemetry")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_get_telemetry_filter_by_machine(client, seed_test_data):
    """Test GET /api/telemetry filtered by machine_id."""
    response = client.get("/api/telemetry?machine_id=CAT-6060-201")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["machine_id"] == "CAT-6060-201"
    assert data[0]["operating_state"] == "EXCAVATING"


def test_get_telemetry_filter_by_operator(client, seed_test_data):
    """Test GET /api/telemetry filtered by operator_id."""
    response = client.get("/api/telemetry?operator_id=OP-101")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    for record in data:
        assert record["operator_id"] == "OP-101"


def test_get_telemetry_filter_by_task_id(client, seed_test_data):
    """Test GET /api/telemetry filtered by task_id."""
    response = client.get("/api/telemetry?task_id=TSK-TEST-02")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["task_id"] == "TSK-TEST-02"


def test_get_telemetry_filter_by_timestamp_range(client, seed_test_data):
    """Test GET /api/telemetry filtered by start_time and end_time."""
    response = client.get("/api/telemetry?start_time=2026-09-20T06:01:00Z&end_time=2026-09-20T06:05:00Z")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["timestamp"] == "2026-09-20T06:01:00Z"


def test_get_telemetry_pagination(client, seed_test_data):
    """Test pagination limit and offset."""
    response = client.get("/api/telemetry?limit=2&offset=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_telemetry_invalid_limit(client):
    """Test invalid request handling: negative limit triggers 422."""
    response = client.get("/api/telemetry?limit=-5")
    assert response.status_code == 422

    response_high = client.get("/api/telemetry?limit=5000")
    assert response_high.status_code == 422


def test_get_telemetry_invalid_offset(client):
    """Test invalid request handling: negative offset triggers 422."""
    response = client.get("/api/telemetry?offset=-1")
    assert response.status_code == 422
