#!/bin/bash

# Master Workflow Orchestration Script
# Usage: bash run_workflow.sh [bench_dir] [max_concurrent]

BENCH_DIR=${1:-/tmp/mcp-benchmark}
MAX_CONCURRENT_NUM=${2:-3}
echo "=========================================================="
echo "Starting Master Workflow"
echo "Benchmark Directory: $BENCH_DIR"
echo "Max Concurrent: $MAX_CONCURRENT_NUM"
echo "=========================================================="

# Track results
declare -A RESULTS

run_step() {
    local step_name=$1
    local command=$2
    
    echo "----------------------------------------------------------"
    echo "[*] Running Step: $step_name"
    echo "Command: $command"
    echo "----------------------------------------------------------"
    
    # Run command and show output in terminal
    eval "$command"
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "[+] Step $step_name: SUCCESS"
        RESULTS[$step_name]="PASSED"
    else
        echo "[-] Step $step_name: FAILED (Exit Code: $exit_code)"
        RESULTS[$step_name]="FAILED"
    fi
}

# Step 1: Download MCP sources
run_step "1_download_sources" "python3 download_mcp_sources.py"

# Step 2: Setup benchmark directory (Equivalent to MCPZoo/setup.sh)
run_step "2_setup_benchmark" "python3 MCPZoo/setup_benchmark.py --bench-dir $BENCH_DIR"

# Step 3: Run RQ1 methods
RQ1_METHODS=("llm_only" "single_agent" "semant_guard")
for method in "${RQ1_METHODS[@]}"; do
    run_step "3_rq1_$method" "python3 MCPSecAgent/exp_rq1.py --bench $BENCH_DIR --method $method --output ./results/rq1/$method --max-concurrent $MAX_CONCURRENT_NUM"
done

# Step 4: Run RQ2
run_step "4_rq2_scan" "python3 MCPSecAgent/exp_rq2.py --bench $BENCH_DIR --output ./results/rq2/scan_with_intent_capability --max-concurrent $MAX_CONCURRENT_NUM"

echo ""
echo "=========================================================="
echo "Workflow Summary"
echo "=========================================================="
printf "%-30s | %-10s\n" "Step" "Result"
echo "----------------------------------------------------------"

# Define order for summary
STEPS=("1_download_sources" "2_setup_benchmark" "3_rq1_llm_only" "3_rq1_single_agent" "3_rq1_semant_guard" "4_rq2_scan")

for step in "${STEPS[@]}"; do
    printf "%-30s | %-10s\n" "$step" "${RESULTS[$step]}"
done

echo "=========================================================="
echo "All steps completed."
