#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
REQUESTED_API_PORT="${API_PORT:-8000}"
REQUESTED_UI_PORT="${UI_PORT:-8501}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="${PYTHON_BIN_FALLBACK:-python3}"
fi

find_available_port() {
  local candidate="$1"
  local reserved_port="${2:-}"

  while (( candidate <= 65535 )); do
    if [[ "$candidate" != "$reserved_port" ]] && "$PYTHON_BIN" -c \
      'import socket, sys; sock = socket.socket(); sock.bind(("127.0.0.1", int(sys.argv[1]))); sock.close()' \
      "$candidate" >/dev/null 2>&1; then
      printf '%s' "$candidate"
      return 0
    fi
    candidate=$((candidate + 1))
  done

  printf 'No free local port found starting at %s\n' "$1" >&2
  return 1
}

API_PORT="$(find_available_port "$REQUESTED_API_PORT")"
UI_PORT="$(find_available_port "$REQUESTED_UI_PORT" "$API_PORT")"
UI_URL="http://127.0.0.1:${UI_PORT}"
API_URL="http://127.0.0.1:${API_PORT}"

cleanup() {
  [[ -n "${API_PID:-}" ]] && kill "$API_PID" 2>/dev/null || true
  [[ -n "${UI_PID:-}" ]] && kill "$UI_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait_for_service() {
  local service_name="$1"
  local service_url="$2"

  if ! curl --fail --silent --show-error \
    --retry 30 \
    --retry-delay 1 \
    --retry-connrefused \
    --retry-max-time 45 \
    "$service_url" >/dev/null; then
    printf 'Unable to start %s at %s\n' "$service_name" "$service_url" >&2
    return 1
  fi
}

open_in_chrome() {
  local browser_bin="${CHROME_BIN:-}"
  if [[ -z "$browser_bin" ]]; then
    for candidate in google-chrome google-chrome-stable chromium chromium-browser; do
      if command -v "$candidate" >/dev/null 2>&1; then
        browser_bin="$candidate"
        break
      fi
    done
  fi

  if [[ -n "$browser_bin" ]]; then
    "$browser_bin" --new-window "$UI_URL" >/dev/null 2>&1 &
    printf 'Opened Chrome at %s\n' "$UI_URL"
  else
    printf 'Chrome was not found. Open %s in a browser.\n' "$UI_URL" >&2
  fi
}

cd "$ROOT_DIR"
"$PYTHON_BIN" -m uvicorn main:app --host 127.0.0.1 --port "$API_PORT" &
API_PID=$!
API_BASE_URL="$API_URL" \
"$PYTHON_BIN" -m streamlit run app/ui/streamlit_app.py \
  --server.headless=true \
  --server.address=127.0.0.1 \
  --server.port="$UI_PORT" \
  --browser.gatherUsageStats=false &
UI_PID=$!

printf 'Lingo Play is running at http://127.0.0.1:%s\n' "$UI_PORT"
printf 'FastAPI docs are at http://127.0.0.1:%s/docs\n' "$API_PORT"
if [[ "$API_PORT" != "$REQUESTED_API_PORT" ]]; then
  printf 'Default API port %s was busy; using %s instead.\n' "$REQUESTED_API_PORT" "$API_PORT"
fi
if [[ "$UI_PORT" != "$REQUESTED_UI_PORT" ]]; then
  printf 'Default UI port %s was busy; using %s instead.\n' "$REQUESTED_UI_PORT" "$UI_PORT"
fi
wait_for_service "FastAPI" "$API_URL/health"
wait_for_service "Streamlit" "$UI_URL"
open_in_chrome
wait "$UI_PID"