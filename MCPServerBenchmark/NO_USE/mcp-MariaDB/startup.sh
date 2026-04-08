#!/bin/bash

# 1. 设置默认端口（如果用户没有输入参数，则使用 8000）
PORT=${1:-8000}

RANDOM_PASSWORD=$(cat /dev/urandom | base64 | tr -d '\n' | head -c 32)
MCP_SERVER_PORT=$PORT MARIADB_PASSWORD=$RANDOM_PASSWORD docker compose up --build -d