#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate the shared virtual environment (~/.venvs/web-apis-env or ./env)
if [ -f "$HOME/.venvs/web-apis-env/bin/activate" ]; then
    source "$HOME/.venvs/web-apis-env/bin/activate"
elif [ -f "$SCRIPT_DIR/env/bin/activate" ]; then
    source "$SCRIPT_DIR/env/bin/activate"
fi

TOTAL_CALLS="${1:-10}"
PARALLEL_WORKERS="${2:-10}"

FLASK_URL="http://127.0.0.1:5000"
FASTAPI_URL="http://127.0.0.1:8000"

# Generate numbers 1..TOTAL_CALLS
generate_calls() {
    local value=0
    while [ "$value" -lt "$TOTAL_CALLS" ]; do
        value=$((value + 1))
        echo "$value"
    done
}

# Execute a single CRUD API call for a given VALUE against ENDPOINT_PREFIX
run_single_call() {
    local endpoint_prefix="$1"
    local val="$2"
    local label="$3"
    local priority=$(( (val % 4) + 1 ))

    local create_resp
    create_resp=$(curl -s -X POST "$endpoint_prefix/tasks/create" \
        -H "Content-Type: application/json" \
        -d "{\"summary\": \"$label Task #$val\", \"priority\": $priority}")

    local task_id
    task_id=$(echo "$create_resp" | grep -o '"id":[[:space:]]*[0-9]*' | head -n1 | grep -o '[0-9]*$')

    if [ -n "$task_id" ]; then
        curl -s "$endpoint_prefix/tasks/$task_id" > /dev/null
        curl -s -X PUT "$endpoint_prefix/tasks/$task_id/update" \
            -H "Content-Type: application/json" \
            -d "{\"summary\": \"$label Task #$val (Updated)\", \"priority\": 1}" > /dev/null
    fi
}

export -f run_single_call

run_target() {
    local var_name="$1"
    local server_name="$2"
    local endpoint_prefix="$3"
    local parallelism="$4"
    local label="$5"

    echo "   -> Testing $server_name ($endpoint_prefix/tasks/*) [Parallelism: -P $parallelism]"

    local start_ns
    start_ns=$(date +%s%N)

    if [ "$parallelism" -eq 1 ]; then
        local value=0
        while [ "$value" -lt "$TOTAL_CALLS" ]; do
            value=$((value + 1))
            run_single_call "$endpoint_prefix" "$value" "$label"
            echo -n "[$value] "
        done
        echo ""
    else
        generate_calls | xargs -r -P "$parallelism" -I VALUE bash -c \
            "run_single_call '$endpoint_prefix' 'VALUE' '$label' && echo -n '[VALUE] '"
        echo ""
    fi

    local end_ns
    end_ns=$(date +%s%N)
    local elapsed_ms=$(( (end_ns - start_ns) / 1000000 ))

    echo "      Time taken ($server_name): ${elapsed_ms} ms"
    eval "${var_name}=${elapsed_ms}"
}

echo "################################################################################"
echo "# Flask (:5000) vs FastAPI (:8000) — Applying All 4 Scenarios to Each Server"
echo "# Calls per test: $TOTAL_CALLS | Simultaneous workers: $PARALLEL_WORKERS"
echo "################################################################################"

# ==============================================================================
# Test Scenario 1: Sequential API calls to sequential API endpoint
# ==============================================================================
echo ""
echo "================================================================================"
echo " Test Scenario 1: Sequential API calls (-P 1) -> Sequential API endpoint (/api/seq)"
echo "================================================================================"
run_target "S1_FLASK_MS"   "Flask   (:5000)" "$FLASK_URL/api/seq"   1 "S1-Flask-Seq"
run_target "S1_FASTAPI_MS" "FastAPI (:8000)" "$FASTAPI_URL/api/seq" 1 "S1-FastAPI-Seq"

# ==============================================================================
# Test Scenario 2: Asynchronous API calls to sequential API endpoint
# ==============================================================================
echo ""
echo "================================================================================"
echo " Test Scenario 2: Asynchronous API calls (xargs -P $PARALLEL_WORKERS) -> Sequential API endpoint (/api/seq)"
echo "================================================================================"
run_target "S2_FLASK_MS"   "Flask   (:5000)" "$FLASK_URL/api/seq"   "$PARALLEL_WORKERS" "S2-Flask-Seq"
run_target "S2_FASTAPI_MS" "FastAPI (:8000)" "$FASTAPI_URL/api/seq" "$PARALLEL_WORKERS" "S2-FastAPI-Seq"

# ==============================================================================
# Test Scenario 3: Sequential API calls to asynchronous API endpoint
# ==============================================================================
echo ""
echo "================================================================================"
echo " Test Scenario 3: Sequential API calls (-P 1) -> Asynchronous API endpoint (/api/async)"
echo "================================================================================"
run_target "S3_FLASK_MS"   "Flask   (:5000)" "$FLASK_URL/api/async"   1 "S3-Flask-Async"
run_target "S3_FASTAPI_MS" "FastAPI (:8000)" "$FASTAPI_URL/api/async" 1 "S3-FastAPI-Async"

# ==============================================================================
# Test Scenario 4: Asynchronous API calls to asynchronous API endpoint
# ==============================================================================
echo ""
echo "================================================================================"
echo " Test Scenario 4: Asynchronous API calls (xargs -P $PARALLEL_WORKERS) -> Asynchronous API endpoint (/api/async)"
echo "================================================================================"
run_target "S4_FLASK_MS"   "Flask   (:5000)" "$FLASK_URL/api/async"   "$PARALLEL_WORKERS" "S4-Flask-Async"
run_target "S4_FASTAPI_MS" "FastAPI (:8000)" "$FASTAPI_URL/api/async" "$PARALLEL_WORKERS" "S4-FastAPI-Async"

echo ""
echo "================================================================================"
echo " BENCHMARK SUMMARY: All 4 Scenarios Applied to Each Server ($TOTAL_CALLS calls each)"
echo "================================================================================"
printf " %-48s | %12s | %12s\n" "Test Scenario" "Flask :5000" "FastAPI :8000"
echo "--------------------------------------------------------------------------------"
printf " %-48s | %9s ms | %9s ms\n" "Scenario 1: Sequential calls -> Sequential API" "$S1_FLASK_MS" "$S1_FASTAPI_MS"
printf " %-48s | %9s ms | %9s ms\n" "Scenario 2: Async calls      -> Sequential API" "$S2_FLASK_MS" "$S2_FASTAPI_MS"
printf " %-48s | %9s ms | %9s ms\n" "Scenario 3: Sequential calls -> Async API"      "$S3_FLASK_MS" "$S3_FASTAPI_MS"
printf " %-48s | %9s ms | %9s ms\n" "Scenario 4: Async calls      -> Async API"      "$S4_FLASK_MS" "$S4_FASTAPI_MS"
echo "================================================================================"
