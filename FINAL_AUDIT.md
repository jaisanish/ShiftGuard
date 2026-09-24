# ShiftGuard Final Audit

## Delivery status

Phases 1–12 and 14 are complete. Phase 13 (AWS deployment) is intentionally skipped because this delivery targets local operation and Docker Compose.

## Verification evidence

Run from the repository root:

```bash
.venv/bin/python -m pytest -q
cd frontend && npm run lint && npm run build
docker compose config
```

The final backend regression suite and frontend production build were run during Phase 14. Docker Compose configuration validates. Docker image pulls may require more time than constrained environments allow; use `docker compose up --build` on a normal local Docker installation.

## Local operation

Development:

```bash
.venv/bin/uvicorn backend.app.main:app --reload
cd frontend && npm run dev
```

Containerized:

```bash
docker compose up --build
```

See [DOCKER.md](DOCKER.md) for ports, volumes, and stop/reset commands.

## Health and deterministic demo

- `GET /health` verifies local API/database connectivity.
- `GET /health/ready` verifies database, anomaly model, ETA model, copilot boundary, and cloud status.
- `GET /api/simulator/demo/scenarios` lists repeatable presentation scenarios.
- `POST /api/simulator/demo/run` with `{ "scenario": "proximity_critical" }` runs a zero-delay deterministic scenario.
- `POST /api/simulator/demo/restore-cloud` ends an offline-sync demonstration.

## Safety and scope boundaries

- Edge safety is deterministic and local; advisory anomaly, ETA, copilot, and coaching features cannot override it.
- The anomaly and ETA artifacts are trained and evaluated on synthetic data only; their reported metrics are not real-world validation.
- The copilot defaults to local retrieval. An optional hosted provider requires explicit environment configuration.
- This demo-oriented project has no user authentication, authorization, TLS termination, or managed secret store. Do not expose it publicly without adding those production controls.
