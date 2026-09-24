# Run ShiftGuard with Docker

From the repository root:

```bash
docker compose up --build
```

Open the operator console at `http://localhost:5173`. The backend API and WebSocket endpoint are available at `http://localhost:8000` and `ws://localhost:8000/ws/telemetry`.

The named `shiftguard_edge_data` volume persists the edge and cloud SQLite files across restarts. To stop the stack, run `docker compose down`. To also remove all demo data, run `docker compose down -v`.

The frontend proxies REST traffic to the backend. The backend remains separately exposed because the browser client’s telemetry WebSocket uses port 8000.

Useful checks:

```bash
curl http://localhost:8000/health/ready
curl http://localhost:8000/api/simulator/demo/scenarios
```

No cloud account or AWS configuration is required.
