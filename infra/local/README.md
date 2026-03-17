# Local Stack

This stack brings up the Greenference V1 control plane and one bootstrap miner:

- Postgres
- Redis
- NATS JetStream
- MinIO
- OCI registry
- Alembic migration job
- Gateway
- Control plane
- Builder
- Validator
- Miner agent

## Bring Up

Run the stack:

```bash
docker compose -f greenference-api/infra/local/docker-compose.yml up -d
```

The migration job runs first and the service containers only start after `alembic upgrade head` succeeds.

## Runtime Defaults

The local stack uses Postgres as the default development path through:

`GREENFERENCE_DATABASE_URL=postgresql+psycopg://greenference:greenference@postgres:5432/greenference`

Runtime dependency URLs are injected for Redis, NATS, MinIO, and the local OCI registry. The `builder`, `control-plane`, and `miner-agent` containers run with background workers enabled. The miner container also bootstraps one default node and continuously reconciles assigned leases, so the full inference happy path can complete without manual reconcile calls.

## Health Checks

Every service exposes:

- `/healthz` for liveness
- `/readyz` for readiness

For `builder`, `control-plane`, and `miner-agent`, `/readyz` also includes worker state so you can confirm the background loop has started and recorded at least one iteration.

Service ports:

- `8000` gateway
- `8001` control-plane
- `8002` validator
- `8003` builder
- `8004` miner-agent

## Smoke Test

After the stack is healthy, run:

```bash
python greenference-api/infra/local/smoke_test.py
```

The smoke test waits for service readiness, registers a user and admin API key, publishes a validator capability for the bootstrap miner, runs build -> workload -> deployment -> inference -> usage, then submits a validator probe result and publishes a weight snapshot.

## Recovery Expectations

The stack is expected to recover these cases cleanly:

- pending workflow events survive service restarts because they are stored in Postgres
- deployments remain queryable after `gateway` or `control-plane` restarts
- usage aggregation continues after a worker restart
- the bootstrap miner reconnects and resumes reconcile loops on restart
