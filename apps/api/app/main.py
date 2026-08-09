import logging
import time
from collections import defaultdict, deque
from pathlib import Path
from uuid import uuid4

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import get_settings
from app.database import create_db_and_tables, engine
from app.routers import analysis, drafts, imports, profiles

settings = get_settings()
app = FastAPI(title=settings.app_name)
logger = logging.getLogger("app.requests")
rate_windows: dict[str, deque[float]] = defaultdict(deque)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_observability_and_limits(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid4()))
    started = time.perf_counter()
    client = request.client.host if request.client else "unknown"
    rate_key = f"{client}:{request.url.path}"

    if request.method == "POST" and request.url.path.endswith("/drafts"):
        now = time.time()
        window = rate_windows[rate_key]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= settings.generation_rate_limit_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Generation rate limit exceeded. Try again shortly."},
                headers={"x-request-id": request_id},
            )
        window.append(now)

    response = await call_next(request)
    duration_ms = int((time.perf_counter() - started) * 1000)
    response.headers["x-request-id"] = request_id
    logger.info(
        "http_request request_id=%s method=%s path=%s status=%s duration_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


@app.get("/api/ready")
def ready() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        current = MigrationContext.configure(connection).get_current_revision()
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    head = ScriptDirectory.from_config(config).get_current_head()
    if current != head and current is not None:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "detail": "Database migration is not at head"},
        )
    return {"status": "ready", "database": "ok"}


app.include_router(profiles.router)
app.include_router(imports.router)
app.include_router(analysis.router)
app.include_router(drafts.router)
