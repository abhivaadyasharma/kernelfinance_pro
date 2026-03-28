#!/bin/bash
# KernelFinance Pro - Unified Startup Script
# Starts the Node.js backend server, then launches the Python frontend.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER_DIR="$SCRIPT_DIR/js-frontend"
export KF_PORT="${KF_PORT:-3721}"
export KF_DB_PATH="${KF_DB_PATH:-$SCRIPT_DIR/kernel_finance_pro.db}"

SERVER_PID=""

cleanup() {
    if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "Stopping server (PID $SERVER_PID)..."
        kill "$SERVER_PID" 2>/dev/null
        wait "$SERVER_PID" 2>/dev/null
    fi
}

trap cleanup EXIT INT TERM

# Install dependencies if needed
if [ ! -d "$SERVER_DIR/node_modules" ]; then
    echo "Installing server dependencies..."
    (cd "$SERVER_DIR" && npm install)
fi

# Start Node.js server in background
echo "Starting KernelFinance server on port $KF_PORT..."
node "$SERVER_DIR/server.js" &
SERVER_PID=$!

# Wait for server to be ready
echo "Waiting for server..."
for i in $(seq 1 12); do
    if curl -sf "http://127.0.0.1:$KF_PORT/api/health" > /dev/null 2>&1; then
        echo "Server ready."
        break
    fi
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        echo "Error: Server failed to start."
        exit 1
    fi
    sleep 0.5
done

if ! curl -sf "http://127.0.0.1:$KF_PORT/api/health" > /dev/null 2>&1; then
    echo "Error: Server did not become ready in time."
    exit 1
fi

# Launch Python frontend (blocks until GUI closes)
echo "Launching KernelFinance Pro..."
python3 "$SCRIPT_DIR/kernel_finance_pro.py"

echo "KernelFinance Pro closed."
