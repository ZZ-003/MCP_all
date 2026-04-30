#!/bin/bash

if ! docker network inspect mcp-shared-network &>/dev/null; then
    echo "Create mcp-shared-network..."
    docker network create --driver bridge mcp-shared-network
fi
export NETWORK_NAME=mcp-shared-network

bench_dir=${1:-/tmp/mcp-benchmark-mali}

set -e
python gen-benchmark/gen_python_mcp.py
python setup_benchmark.py --bench-dir $bench_dir -t 10 setup
python gen_ground_truth.py
