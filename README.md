# Flask vs. FastAPI Todo API Benchmarking

A side-by-side comparison and benchmarking suite for a **Todo Task Management REST API** implemented in both **Flask** (sequential/synchronous endpoint on port `5000`) and **FastAPI** (asynchronous endpoint on port `8000`), backed by a shared **SQLite (`todos.db`)** relational database using a top-down handler architecture.

---

## Project Structure

```text
web-apis-with-python/
├── README.md                    # Documentation: running servers & benchmarks
├── PLAN.md                      # Master project plan & progress tracker
├── flask_requeriments.txt       # Flask dependencies
├── fastapi_requeriments.txt     # FastAPI dependencies
├── flask_api_controller.py      # Sequential Flask Todo API controller (Port 5000)
├── fastapi_api_controller.py    # Asynchronous FastAPI Todo API controller (Port 8000)
├── run_servers.sh               # Parallel server launcher (xargs -r -P 2)
├── benchmark_parallel.sh        # 4-Scenario benchmark suite (xargs -r -P)
├── todos.db                     # Shared SQLite database (WAL mode, auto-created)
└── model/
    ├── __init__.py
    ├── model.py                 # Pydantic models: ID, Task, TaskList
    ├── swagger.py               # OpenAPI 3.0 spec & Swagger UI HTML for Flask
    └── task_service.py          # Top-down task service for SQLite (sync & async)
```

---

## 1. Setup & Dependencies

Create the shared virtual environment in your Linux home directory (`~/.venvs/web-apis-env`), activate it, and install both requirement files:

```bash
# Clean up any partial local env folder if present
rm -rf env

# Create virtual environment in your native Linux home directory
python3 -m venv ~/.venvs/web-apis-env

# Activate virtual environment
source ~/.venvs/web-apis-env/bin/activate

# Install Flask and FastAPI dependencies
pip install -r flask_requeriments.txt -r fastapi_requeriments.txt
```

> **Why `~/.venvs/web-apis-env` instead of `./env`?**
> When this project directory is hosted on a mounted/shared filesystem (such as WSL `9p`/SMB network mounts, VirtualBox shared folders, or exFAT/NTFS drives), Linux symbolic links are blocked by the filesystem driver. Running `python3 -m venv env` inside the project folder fails with `Error: [Errno 1] Operation not permitted: 'lib' -> '.../env/lib64'` (even with `--copies`, 64-bit Linux `venv` still attempts to symlink `lib64 -> lib`). Storing the virtual environment in `~/.venvs/web-apis-env` places it on the native Linux `ext4` filesystem where symlinks, file permissions, and binary executions work without restrictions.

---

## 2. How to Run the Servers

### Option A: Run Both Servers in Parallel (Recommended)
Use [`run_servers.sh`](file:///home/toor/DEVOPS_DEV/web-apis-with-python/run_servers.sh), which activates `~/.venvs/web-apis-env` (or `./env` if present) and uses `xargs -r -P 2` to run Flask (`:5000`) and FastAPI (`:8000`) simultaneously:

```bash
./run_servers.sh
```
Press `Ctrl+C` to stop both servers together.

---

### Option B: Run Each Server Individually

#### 1. Run the Flask Server (Sequential API on Port `5000`)
```bash
source ~/.venvs/web-apis-env/bin/activate
python flask_api_controller.py
```
- **Base URL**: `http://127.0.0.1:5000`
- **Swagger UI**: `http://127.0.0.1:5000/api/doc`
- **OpenAPI Spec**: `http://127.0.0.1:5000/api/openapi.json`

#### 2. Run the FastAPI Server (Asynchronous API on Port `8000`)
```bash
source ~/.venvs/web-apis-env/bin/activate
python fastapi_api_controller.py
# Or directly with uvicorn:
uvicorn fastapi_api_controller:app --host 0.0.0.0 --port 8000
```
- **Base URL**: `http://127.0.0.1:8000`
- **Swagger UI**: `http://127.0.0.1:8000/api/doc`
- **OpenAPI Spec**: `http://127.0.0.1:8000/api/openapi.json`

---

## 3. API Specifications & Endpoints

Each task follows the schema defined in [`model/model.py`](file:///home/toor/DEVOPS_DEV/web-apis-with-python/model/model.py):
- **`id`**: Unique integer identifier (`ID = NewType("id", int)`)
- **`summary`**: Task description (`str`)
- **`priority`**: Integer priority from `1` to `4` (`1` being highest)

Both Flask (`:5000`) and FastAPI (`:8000`) expose the exact same endpoints and share `todos.db`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/doc` | Interactive **Swagger UI** documentation |
| `GET` | `/api/tasks` | Fetch the list of all tasks |
| `GET` | `/api/tasks/{id}` | Fetch a single task by `id` |
| `POST` | `/api/tasks/create` | Create a new task (`{"summary": "...", "priority": 1}`) |
| `PUT` | `/api/tasks/{id}/update` | Update `summary` and `priority` of task `id` |
| `DELETE` | `/api/tasks/{id}/delete` | Delete a task by `id` |

### Quick `curl` Examples
```bash
# 1. Create a task (on Flask :5000)
curl -X POST http://127.0.0.1:5000/api/tasks/create \
  -H "Content-Type: application/json" \
  -d '{"summary": "Write API documentation", "priority": 1}'

# 2. Fetch all tasks (from FastAPI :8000 — reads the same shared todos.db)
curl http://127.0.0.1:8000/api/tasks

# 3. Fetch task #1 by ID
curl http://127.0.0.1:8000/api/tasks/1

# 4. Update task #1
curl -X PUT http://127.0.0.1:8000/api/tasks/1/update \
  -H "Content-Type: application/json" \
  -d '{"summary": "Update API documentation", "priority": 2}'

# 5. Delete task #1
curl -X DELETE http://127.0.0.1:5000/api/tasks/1/delete
```

---

## 4. How to Run the Benchmark

### What the Benchmark Does
The benchmark script ([`benchmark_parallel.sh`](file:///home/toor/DEVOPS_DEV/web-apis-with-python/benchmark_parallel.sh)) applies **all 4 Test Scenarios to each server** (**Flask on port `5000`** and **FastAPI on port `8000`**) against the shared SQLite database (`todos.db`).

Both servers expose:
- **Sequential (Synchronous) API endpoints**: `/api/seq/tasks/*` (uses synchronous blocking `task_service.*_sync`)
- **Asynchronous API endpoints**: `/api/async/tasks/*` (uses non-blocking `await task_service.*`)

For every single iteration (`1..10`), a client worker performs a 3-step CRUD workflow:
1. **`POST .../tasks/create`** — Creates a new task in `todos.db` and captures its `id`.
2. **`GET .../tasks/{id}`** — Fetches the newly created task by `id` from `todos.db`.
3. **`PUT .../tasks/{id}/update`** — Updates the task's `summary` and `priority` in `todos.db`.

### All 4 Test Scenarios Applied to Both Servers (`Flask :5000` & `FastAPI :8000`)

| Scenario | Client Call Mode | Target Server Endpoint | Applied To | Expected Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Test Scenario 1** | **Sequential API calls** (`-P 1`, loop `1..10`) | **Sequential API endpoint** (`/api/seq/tasks/*`) | Both **Flask `:5000`** & **FastAPI `:8000`** | Client sends 10 calls one after another to the synchronous endpoint on each server. |
| **Test Scenario 2** | **Asynchronous API calls** (`xargs -r -P 10`) | **Sequential API endpoint** (`/api/seq/tasks/*`) | Both **Flask `:5000`** & **FastAPI `:8000`** | Client sends 10 calls simultaneously to the synchronous endpoint on each server; server still processes 1 at a time, with reduced client dispatch overhead. |
| **Test Scenario 3** | **Sequential API calls** (`-P 1`, loop `1..10`) | **Asynchronous API endpoint** (`/api/async/tasks/*`) | Both **Flask `:5000`** & **FastAPI `:8000`** | Client sends 10 calls one after another to the asynchronous endpoint on each server. |
| **Test Scenario 4** | **Asynchronous API calls** (`xargs -r -P 10`) | **Asynchronous API endpoint** (`/api/async/tasks/*`) | Both **Flask `:5000`** & **FastAPI `:8000`** | Client sends 10 calls simultaneously to the asynchronous endpoint on each server — FastAPI's ASGI event loop processes all 10 concurrently (~6x–8x faster), while Flask's synchronous WSGI server still processes them one at a time. |

---

### Running the Benchmark
With both servers running (e.g., via `./run_servers.sh` in Terminal 1), open a second terminal and run:

```bash
./benchmark_parallel.sh
```

### Customizing Calls & Parallel Workers
By default, the script runs **10 API calls** per scenario and uses **10 parallel workers** (`xargs -r -P 10`) for the simultaneous scenarios. You can pass custom values as arguments:

```bash
# Usage: ./benchmark_parallel.sh <TOTAL_CALLS> <PARALLEL_WORKERS>
./benchmark_parallel.sh 20 8
```
