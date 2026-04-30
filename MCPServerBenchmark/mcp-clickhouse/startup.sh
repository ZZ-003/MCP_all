#!/bin/bash

PORT=${1:-8000}

RANDOM_PASSWORD=$(cat /dev/urandom | base64 | tr -d '\n' | head -c 32)
MCP_SERVER_PORT=$PORT CLICKHOUSE_PASSWORD=$RANDOM_PASSWORD docker compose up --build -d