#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate the shared virtual environment (~/.venvs/web-apis-env or ./env)
if [ -f "$HOME/.venvs/web-apis-env/bin/activate" ]; then
    VENV_ACTIVATE="$HOME/.venvs/web-apis-env/bin/activate"
elif [ -f "$SCRIPT_DIR/env/bin/activate" ]; then
    VENV_ACTIVATE="$SCRIPT_DIR/env/bin/activate"
else
    echo "Error: Virtual environment not found at ~/.venvs/web-apis-env or ./env" >&2
    exit 1
fi
source "$VENV_ACTIVATE"
export PYTHONUNBUFFERED=1

echo "============================================================"
echo " Flask   (Sync,  Debug=ON) : http://127.0.0.1:5000/api/tasks"
echo " Flask   Swagger UI        : http://127.0.0.1:5000/api/doc"
echo " FastAPI (Async, Debug=ON) : http://127.0.0.1:8000/api/tasks"
echo " FastAPI Swagger UI        : http://127.0.0.1:8000/api/doc"
echo " Shared SQLite DB          : $SCRIPT_DIR/todos.db"
echo "============================================================"

cleanup() {
    trap - SIGINT SIGTERM EXIT
    kill 0 2>/dev/null || true
}
trap cleanup SIGINT SIGTERM EXIT

printf "%s\n" \
    "python -u flask_api_srv.py" \
    "python -u fastapi_api_srv.py" | \
    xargs -r -P 2 -I CMD bash -c "source '$VENV_ACTIVATE' && CMD"
