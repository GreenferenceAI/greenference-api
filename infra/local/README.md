# Local Stack

This stack brings up the base Greenference dependencies:

- Postgres
- Redis
- NATS JetStream
- MinIO
- OCI registry
- Gateway
- Control plane
- Validator
- Builder
- Miner agent
- Alembic migration job

Run:

```bash
docker compose -f greenference-api/infra/local/docker-compose.yml up -d
```


Each service package can then be started with its own FastAPI entrypoint.

The local stack uses Postgres as the default development path through:

`GREENFERENCE_DATABASE_URL=postgresql+psycopg://greenference:greenference@postgres:5432/greenference`

Service ports:

- `8000` gateway
- `8001` control-plane
- `8002` validator
- `8003` builder
- `8004` miner-agent
