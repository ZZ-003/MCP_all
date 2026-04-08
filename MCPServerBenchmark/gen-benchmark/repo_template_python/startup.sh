#!/bin/bash

# 1. 设置默认端口（如果用户没有输入参数，则使用 8000）
PORT=${1:-8000}

MCP_SERVER_PORT=$PORT docker compose up --build -d