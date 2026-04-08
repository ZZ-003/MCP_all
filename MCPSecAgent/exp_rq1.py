import argparse
from dotenv import load_dotenv
load_dotenv()
import asyncio

from utils.coroutine import batch_code_repo_scan
from llm_only import llm_only_scan
from single_agent import single_agent_scan
from semant_guard.experiment_scan import agent_with_ltm_scan


METHOD_MAP = {
    "llm_only": llm_only_scan,
    "single_agent": single_agent_scan,
    "semant_guard": agent_with_ltm_scan,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch scan code repositories with different agents")
    parser.add_argument("--bench", "-i", default="/tmp/mcp-benchmark", type=str, help="Path to the benchmark directory")
    parser.add_argument("--output", "-o", type=str, help="Path to the output directory")
    parser.add_argument("--method", "-m", type=str, choices=["llm_only", "single_agent", "semant_guard"], default="llm_only", help="Type of agent to use for scanning")
    parser.add_argument("--max-concurrent", "-t", type=int, default=3, help="Maximum concurrent scans")
    args = parser.parse_args()

    scan_func = METHOD_MAP.get(args.method)
    if scan_func is None:
        raise ValueError(f"Unknown method: {args.method}")
    output_dir = args.output
    if output_dir is None:
        output_dir = f"./results/rq1/{args.method}"
    # batch_code_repo_scan(scan_func, args.bench, output_dir, args.max_concurrent)
    asyncio.run(batch_code_repo_scan(scan_func, args.bench, output_dir, args.max_concurrent))