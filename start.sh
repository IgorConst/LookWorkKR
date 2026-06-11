#!/bin/bash

# Проверяем, не запущен ли уже процесс
if [ -f lwk.pid ]; then
    PID=$(cat lwk.pid)
    if ps -p $PID > /dev/null; then
        echo "LWK already running with PID $PID"
        exit 1
    fi
fi

# Запускаем в фоне
cd "$(dirname "$0")"
nohup .venv/bin/python -m lwk > lwk.log 2>&1 &

# Сохраняем PID
echo $! > lwk.pid
echo "LWK started with PID $!"
echo "Logs: tail -f lwk.log"