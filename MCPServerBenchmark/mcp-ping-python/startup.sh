#!/bin/bash

PORT=${1:-8000}

MCP_SERVER_PORT=$PORT docker compose up --build -d