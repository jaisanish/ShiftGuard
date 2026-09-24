"""Phase 11 deterministic demo API tests."""

import backend.app.api.simulator as simulator_api


def test_demo_catalog_and_deterministic_run(client, monkeypatch):
    catalog = client.get("/api/simulator/demo/scenarios")
    assert catalog.status_code == 200
    ids = {item["id"] for item in catalog.json()}
    assert {"normal", "proximity_critical", "eta_delay", "offline_sync"}.issubset(ids)

    async def fake_injection(scenario, machine_id=None, frame_delay_seconds=0):
        assert scenario == "normal"
        assert frame_delay_seconds == 0
        return 7

    monkeypatch.setattr(simulator_api, "_run_hazard_injection", fake_injection)
    run = client.post("/api/simulator/demo/run", json={"scenario": "normal"})
    assert run.status_code == 200
    body = run.json()
    assert body["status"] == "completed"
    assert body["frames_processed"] == 7
    assert body["expected"]

    status = client.get("/api/simulator/demo/status")
    assert status.status_code == 200
    assert status.json()["run_id"] == body["run_id"]


def test_offline_demo_can_restore_cloud(client, monkeypatch):
    async def fake_injection(*args, **kwargs):
        return 2

    monkeypatch.setattr(simulator_api, "_run_hazard_injection", fake_injection)
    run = client.post("/api/simulator/demo/run", json={"scenario": "offline_sync"})
    assert run.status_code == 200
    assert run.json()["cloud_forced_offline"] is True

    restore = client.post("/api/simulator/demo/restore-cloud")
    assert restore.status_code == 200
    assert restore.json()["cloud_connected"] is True
