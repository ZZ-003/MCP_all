#!/bin/bash

bench_dir=${1:-/tmp/mcp-benchmark}

set -e
python setup_benchmark.py --bench-dir $bench_dir
