def test_get_tasks_all(client, seed_test_data):
    """Test GET /api/tasks returns all seeded tasks."""
    response = client.get("/api/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    task_ids = [t["task_id"] for t in data]
    assert "TSK-TEST-01" in task_ids
    assert "TSK-TEST-02" in task_ids


def test_get_tasks_filter_by_machine(client, seed_test_data):
    """Test GET /api/tasks filtered by machine_id."""
    response = client.get("/api/tasks?machine_id=CAT-6060-201")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["task_id"] == "TSK-TEST-02"
    assert data[0]["task_type"] == "OVERBURDEN_REMOVAL"


def test_get_tasks_filter_by_operator(client, seed_test_data):
    """Test GET /api/tasks filtered by operator_id."""
    response = client.get("/api/tasks?operator_id=OP-101")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["task_id"] == "TSK-TEST-01"


def test_get_tasks_filter_by_type(client, seed_test_data):
    """Test GET /api/tasks filtered by task_type."""
    response = client.get("/api/tasks?task_type=ORE_HAULING")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["task_id"] == "TSK-TEST-01"


def test_get_task_by_id_success(client, seed_test_data):
    """Test GET /api/tasks/{task_id} returns single task."""
    response = client.get("/api/tasks/TSK-TEST-01")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "TSK-TEST-01"
    assert data["operator_skill"] == "EXPERT"
    assert data["weather"] == "CLEAR"


def test_get_task_by_id_not_found(client, seed_test_data):
    """Test GET /api/tasks/{task_id} with invalid ID returns 404."""
    response = client.get("/api/tasks/TSK-DOES-NOT-EXIST")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_get_machines_endpoint(client, seed_test_data):
    """Test GET /api/machines returns summarized fleet."""
    response = client.get("/api/machines")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    machine_ids = [m["machine_id"] for m in data]
    assert "CAT-797F-101" in machine_ids
    assert "CAT-6060-201" in machine_ids

    # Verify latest attributes
    truck = next(m for m in data if m["machine_id"] == "CAT-797F-101")
    assert truck["latest_state"] == "HAULING_LOADED"
    assert truck["latest_speed_kmh"] == 32.0


def test_get_operators_endpoint(client, seed_test_data):
    """Test GET /api/operators returns summarized operators."""
    response = client.get("/api/operators")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    op_ids = [op["operator_id"] for op in data]
    assert "OP-101" in op_ids
    assert "OP-103" in op_ids

    op101 = next(op for op in data if op["operator_id"] == "OP-101")
    assert op101["operator_skill"] == "EXPERT"
    assert op101["assigned_machine_id"] == "CAT-797F-101"


def test_tasks_invalid_pagination(client):
    """Test invalid request handling: negative limit triggers 422."""
    response = client.get("/api/tasks?limit=-1")
    assert response.status_code == 422
