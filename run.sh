#!/usr/bin/env bash
#
# Star Business — Python economy kernel launcher.
#
# Wraps the environment setup (interpreter + PYTHONPATH) so you can run the
# kernel, the service, or the tests with one command.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Pick the interpreter: the system Python 3.12 can dlopen Numba/LLVM's dylibs.
# (The bundled dsh-runtime Python is a hardened binary and cannot.)
if [ -n "${ECONOMY_PY:-}" ]; then
  PY="$ECONOMY_PY"
elif [ -x "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3" ]; then
  PY="/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"
else
  PY="python3"
fi

export PYTHONPATH="$ROOT/.pydeps:$ROOT"
cd "$ROOT"

usage() {
  cat <<'EOF'
Star Business — economy kernel launcher

Usage:
  ./run.sh run   [--seed N] [--ticks N] [--cfg JSON] [--out PATH]   headless run
  ./run.sh serve [--host H] [--port P]                              start backend + open browser UI
  ./run.sh test                                                      Python unit tests

Examples:
  ./run.sh run --seed 137 --ticks 30 --cfg '{"consumerCount":500,"t2FirmCount":1000}'
  ./run.sh serve                       # full population (lazy reset ~6s)
  ECONOMY_CFG='{"endUserCount":500,"t2FirmCount":1000}' ./run.sh serve
  ./run.sh test
EOF
}

if [ ! -d "$ROOT/.pydeps" ]; then
  echo "error: $ROOT/.pydeps not found. Install the Python dependencies first:" >&2
  echo "  \"$PY\" -m pip install --target \"$ROOT/.pydeps\" 'numpy<2.6' numba fastapi uvicorn" >&2
  exit 1
fi

case "${1:-}" in
  run)
    shift
    exec "$PY" -W ignore -m economy.cli.main run "$@"
    ;;
  serve)
    shift
    HOST="127.0.0.1"
    PORT=8000
    while [ $# -gt 0 ]; do
      case "$1" in
        --host) HOST="$2"; shift 2 ;;
        --port) PORT="$2"; shift 2 ;;
        *) echo "unknown arg: $1" >&2; exit 1 ;;
      esac
    done
    URL="http://${HOST}:${PORT}/index.html"
    echo "Backend + UI:  ${URL}"
    echo "WebSocket:     ws://${HOST}:${PORT}/ws   (keep this window open; Ctrl+C to stop)"
    # Open the browser only once the backend is actually listening (the JIT
    # warm-up delays uvicorn by ~10 s, so a fixed sleep opens too early).
    (
      for _ in $(seq 1 90); do
        if curl -s -o /dev/null "http://${HOST}:${PORT}/health" 2>/dev/null; then break; fi
        sleep 1
      done
      if command -v open >/dev/null 2>&1; then open "$URL"
      elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL"; fi
    ) &
    exec "$PY" -W ignore -m economy.cli.main serve --host "$HOST" --port "$PORT"
    ;;
  test)
    "$PY" -W ignore tests/py/test_rng.py
    "$PY" -W ignore tests/py/test_kernel.py
    "$PY" -W ignore tests/py/test_review_fixes.py
    ;;
  *)
    usage
    exit 1
    ;;
esac
