#!/bin/bash

# Master Workflow Orchestration Script
# Usage: bash run_workflow.sh [bench_dir]

BENCH_DIR=${1:-/tmp/mcp-benchmark}
LOG_DIR="./logs/workflow_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

echo "=========================================================="
echo "Starting Master Workflow"
echo "Log Directory: $LOG_DIR"
echo "Benchmark Directory: $BENCH_DIR"
echo "=========================================================="

# Track results
declare -A RESULTS
declare -A LOGS

run_step() {
    local step_name=$1
    local command=$2
    local log_file="$LOG_DIR/${step_name}.log"
    
    echo -n "[*] Running Step: $step_name... "
    LOGS[$step_name]=$log_file
    
    # Run command and capture output
    eval "$command" > "$log_file" 2>&1
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "SUCCESS"
        RESULTS[$step_name]="PASSED"
    else
        echo "FAILED (Exit Code: $exit_code)"
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
    run_step "3_rq1_$method" "python3 MCPSecAgent/exp_rq1.py --bench $BENCH_DIR --method $method"
done

# Step 4: Run RQ2
run_step "4_rq2_scan" "python3 MCPSecAgent/exp_rq2.py --bench $BENCH_DIR"

echo ""
echo "=========================================================="
echo "Workflow Summary"
echo "=========================================================="
printf "%-30s | %-10s | %s\n" "Step" "Result" "Log File"
echo "----------------------------------------------------------"

# Define order for summary
STEPS=("1_download_sources" "2_setup_benchmark" "3_rq1_llm_only" "3_rq1_single_agent" "3_rq1_semant_guard" "4_rq2_scan")

for step in "${STEPS[@]}"; do
    printf "%-30s | %-10s | %s\n" "$step" "${RESULTS[$step]}" "${LOGS[$step]}"
done

echo "=========================================================="
echo "All steps completed. Check logs for details."
