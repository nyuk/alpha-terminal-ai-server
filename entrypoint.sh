#!/bin/sh

# Start uvicorn in background
uvicorn main:app --host 0.0.0.0 --port ${PORT:-33333} &
SERVER_PID=$!

# Wait for server to be ready
echo "Waiting for server to start..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:${PORT:-33333}/docs > /dev/null 2>&1; then
        echo "Server is up. Running stock sync..."
        curl -sf http://localhost:${PORT:-33333}/stocks/sync && echo "sync done"
        curl -sf http://localhost:${PORT:-33333}/stocks/sync-market && echo "sync-market done"
        break
    fi
    sleep 2
done

# Keep server in foreground
wait $SERVER_PID
