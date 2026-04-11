import os
import shutil
import argparse
from pathlib import Path


ROOT_DIR = Path(__file__).parent


def setup_bench_dir(bench_dir: str) -> Path:
    BENCH_DIR = Path(bench_dir)
    
    if BENCH_DIR.exists():
        shutil.rmtree(BENCH_DIR)
    BENCH_DIR.mkdir(parents=True, exist_ok=True)

    for mcp_dir in ROOT_DIR.glob("mcp-*"):
        if mcp_dir.is_dir():
            print(f"Setting up {mcp_dir.name}")
            mcp_tmp_dir = BENCH_DIR / mcp_dir.name / "repo"
            mcp_tmp_dir.mkdir(parents=True, exist_ok=True)
            proj_poc_dir = BENCH_DIR / mcp_dir.name / "poc"
            proj_poc_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(mcp_dir, mcp_tmp_dir, dirs_exist_ok=True)

    return BENCH_DIR


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup MCP benchmark servers")
    parser.add_argument("--bench-dir", type=str, default="/tmp/mcp-benchmark", help="Directory for benchmark setup")
    args = parser.parse_args()

    bench_dir = setup_bench_dir(args.bench_dir)
