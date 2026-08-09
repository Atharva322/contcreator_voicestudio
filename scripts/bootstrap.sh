#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  python -m venv .venv
fi

if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
else
  PYTHON_BIN=".venv/Scripts/python.exe"
fi

"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r apps/api/requirements.txt

npm ci --prefix apps/web

if [ ! -f "apps/api/.env" ]; then
  cp apps/api/.env.example apps/api/.env
fi

if [ ! -f "apps/web/.env.local" ]; then
  cp apps/web/.env.example apps/web/.env.local
fi

cat <<'EOF'

Bootstrap complete.

Next:
  source .venv/bin/activate
  npm run dev:api
  npm run dev:web

Validate:
  npm run verify
EOF
