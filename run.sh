#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
API_PORT="${API_PORT:-8000}"
UI_PORT="${UI_PORT:-8501}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="${PYTHON_BIN_FALLBACK:-python3}"
fi

cleanup() {
  [[ -n "${API_PID:-}" ]] && kill "$API_PID" 2>/dev/null || true
  [[ -n "${UI_PID:-}" ]] && kill "$UI_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

cd "$ROOT_DIR"
"$PYTHON_BIN" -m uvicorn main:app --host 127.0.0.1 --port "$API_PORT" &
API_PID=$!
"$PYTHON_BIN" -m streamlit run app/ui/streamlit_app.py \
  --server.headless=true \
  --server.address=127.0.0.1 \
  --server.port="$UI_PORT" \
  --browser.gatherUsageStats=false &
UI_PID=$!

printf 'Lingo Play is running at http://127.0.0.1:%s\n' "$UI_PORT"
printf 'FastAPI docs are at http://127.0.0.1:%s/docs\n' "$API_PORT"
wait "$UI_PID"