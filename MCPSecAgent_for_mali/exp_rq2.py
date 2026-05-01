import argparse
from dotenv import load_dotenv
load_dotenv()
import asyncio

from utils.coroutine import batch_code_repo_scan
from semant_guard.workflow import static_scan_benchmark


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch scan code repositories with different agents")
    parser.add_argument("--bench", "-i", default="/tmp/mcp-benchmark-mali", type=str, help="Path to the benchmark directory")
    parser.add_argument("--output", "-o", type=str, help="Path to the output directory")
    parser.add_argument("--max-concurrent", "-t", type=int, default=1, help="Maximum concurrent scans")
    args = parser.parse_args()

    output_dir = args.output
    if output_dir is None or len(output_dir.strip()) == 0:
        output_dir = f"./results/rq2/scan_with_intent_capability"
    # batch_code_repo_scan(static_scan_benchmark, args.bench, output_dir, args.max_concurrent)
    asyncio.run(batch_code_repo_scan(static_scan_benchmark, args.bench, output_dir, args.max_concurrent))

    # 784 + 11 = 795 / 800 