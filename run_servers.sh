#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$HOME/.venvs/web-apis-env"
VENV_ACTIVATE="$VENV_DIR/bin/activate"

# Create the virtual environment at ~/.venvs/web-apis-env if it does not exist
if [ ! -f "$VENV_ACTIVATE" ]; then
    echo "==> Creating virtual environment at $VENV_DIR ..."
    mkdir -p "$HOME/.venvs"
    if ! python3 -m venv "$VENV_DIR" 2>/dev/null; then
        echo "==> Installing python3-venv ..."
        rm -rf "$VENV_DIR"
        if command -v apt-get >/dev/null 2>&1; then
            sudo apt-get update || true
            sudo apt-get install -y python3-venv python3-pip
        elif command -v dnf >/dev/null 2>&1; then
            sudo dnf install -y python3-virtualenv python3-pip
        fi
        python3 -m venv "$VENV_DIR"
    fi
fi

source "$VENV_ACTIVATE"

# Ensure all required packages for both Flask and FastAPI servers are installed
if ! python -c "import flask, fastapi, uvicorn, asgiref, pydantic" >/dev/null 2>&1; then
    echo "==> Installing Python dependencies into $VENV_DIR ..."
    pip install --upgrade pip
    [ -f "$SCRIPT_DIR/requirements.txt" ] && pip install -r "$SCRIPT_DIR/requirements.txt"
    [ -f "$SCRIPT_DIR/flask_requeriments.txt" ] && pip install -r "$SCRIPT_DIR/flask_requeriments.txt"
    [ -f "$SCRIPT_DIR/fastapi_requeriments.txt" ] && pip install -r "$SCRIPT_DIR/fastapi_requeriments.txt"
fi

export PYTHONUNBUFFERED=1

echo "============================================================"
echo " Flask   (Sync,  Debug=ON) : http://127.0.0.1:8080/api/tasks"
echo " Flask   Swagger UI        : http://127.0.0.1:8080/api/doc"
echo " FastAPI (Async, Debug=ON) : http://127.0.0.1:8090/api/tasks"
echo " FastAPI Swagger UI        : http://127.0.0.1:8090/api/doc"
echo " Shared SQLite DB (Local)  : ${TASK_SERVICE_DB_PATH:-/tmp/web-apis-with-python-benchmark/todos.db}"
echo "============================================================"

cleanup() {
    trap - SIGINT SIGTERM EXIT
    kill 0 2>/dev/null || true
}
trap cleanup SIGINT SIGTERM EXIT

printf "%s\n" \
    "python -u flask_api_controller.py" \
    "python -u fastapi_api_controller.py" | \
    xargs -r -P 2 -I CMD bash -c "source '$VENV_ACTIVATE' && CMD"
