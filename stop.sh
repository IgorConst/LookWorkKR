#!/bin/bash

if [ ! -f lwk.pid ]; then
    echo "LWK is not running (no PID file)"
    exit 1
fi

PID=$(cat lwk.pid)

if ps -p $PID > /dev/null; then
    echo "Stopping LWK (PID $PID)..."
    kill $PID
    rm lwk.pid
    echo "LWK stopped"
else
    echo "LWK is not running (stale PID file)"
    rm lwk.pid
fi