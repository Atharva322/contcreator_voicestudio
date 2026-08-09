# Deployment

Creator Voice Studio remains local-first by default. The deployment foundation supports a single-instance hosted demo with a hosted FastAPI API, a hosted Next.js frontend, Postgres, and optional OpenAI.

## Required Configuration

- `DATABASE_URL`: use Postgres for hosted demos, for example `postgresql+psycopg://...`.
- `CORS_ORIGINS`: set explicit frontend origins. Do not use `*` for public demos.
- `OPENAI_API_KEY`: optional. If omitted, deterministic heuristic fallback remains available.
- `OPENAI_TIMEOUT_SECONDS`: single OpenAI call timeout before fallback.
- `MAX_IMPORT_CHARS`: maximum pasted/import payload size.
- `GENERATION_RATE_LIMIT_PER_MINUTE`: simple in-memory single-instance generation limit.

## API Container

Build:

```bash
docker build -f apps/api/Dockerfile -t creator-voice-api .
```

Run locally against SQLite:

```bash
docker run --rm -p 8000:8000 -e DATABASE_URL=sqlite:///./creator_voice.db creator-voice-api
```

For Postgres simulation:

```bash
docker compose up --build
```

## Migrations

Run migrations as a release step before serving traffic:

```bash
DATABASE_URL=postgresql+psycopg://creator:creator@localhost:5432/creator_voice \
  python -m alembic -c apps/api/alembic.ini upgrade head
```

Do not run migrations concurrently from multiple replicas.

## Health

- `/api/health`: process is alive.
- `/api/ready`: database is reachable and, when versioned, at migration head.

## Frontend

Set `NEXT_PUBLIC_API_BASE_URL` at build/deploy time to the hosted API URL.

No vendor deployment is configured in this repository.
