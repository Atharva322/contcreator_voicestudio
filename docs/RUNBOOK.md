# Runbook

## Readiness Fails

1. Check `DATABASE_URL`.
2. Run `npm run db:current`.
3. Run `npm run db:upgrade` if the database is behind migration head.
4. Confirm the database accepts `SELECT 1`.

## CORS Failures

Set `CORS_ORIGINS` to the exact frontend origins, comma-separated:

```env
CORS_ORIGINS=https://your-frontend.example
```

## Fallback Verification

Unset `OPENAI_API_KEY`, start the API, then run:

```bash
npm run smoke:api
```

The smoke test should complete through style analysis and draft generation with heuristic fallback.

## Oversized Imports

If imports return `413`, reduce the pasted/export payload or raise `MAX_IMPORT_CHARS` intentionally for that environment.

## Rate Limits

Draft generation uses a simple in-memory per-route/client limit. It is suitable only for a single-instance demo. For multi-instance production, move rate limiting to an edge/service layer.

## Backups And Rollback

Before migration, back up the target database. For SQLite, copy the `.db` file. For Postgres, use the platform backup or `pg_dump`.

Rollback policy is restore-from-backup for data migrations. The current Alembic migrations are forward-only for integrity changes.

## Secret Rotation

Rotate `OPENAI_API_KEY` in the hosting secret manager. Never commit secrets to `.env`, Docker images, logs, or docs.
