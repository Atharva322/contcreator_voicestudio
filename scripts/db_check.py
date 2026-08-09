from __future__ import annotations

import sys
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = ROOT / "apps" / "api" / "alembic.ini"
sys.path.insert(0, str(ROOT / "apps" / "api"))


def main() -> int:
    config = Config(str(ALEMBIC_INI))
    script = ScriptDirectory.from_config(config)
    head = script.get_current_head()
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        from app.config import get_settings

        url = get_settings().database_url

    engine = create_engine(url)
    with engine.connect() as connection:
        current = MigrationContext.configure(connection).get_current_revision()

    if current != head:
        print(f"Database migration mismatch: current={current!r}, head={head!r}", file=sys.stderr)
        return 1

    print(f"Database is at migration head {head}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
