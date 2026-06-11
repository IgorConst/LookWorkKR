#!/bin/bash

if [ ! -f lwk.log ]; then
    echo "Log file not found"
    exit 1
fi

tail -f lwk.log