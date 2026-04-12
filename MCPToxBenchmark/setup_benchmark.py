import os
import json
import uuid
import socket
import shutil
import subprocess
import random
import argparse
from typing import Literal
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


ROOT_DIR = Path(__file__).parent
PORT_SET = set()
FLAG_MAP = {}

OUTPUT_DIR = ROOT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SERVICE_DIR = ROOT_DIR / "service"


def setup_bench_dir(bench_dir: str) -> Path:
    BENCH_DIR = Path(bench_dir)

    if os.path.exists(BENCH_DIR):
        shutil.rmtree(BENCH_DIR)
    BENCH_DIR.mkdir(parents=True, exist_ok=True)

    for all_gen_mcp_dir in (ROOT_DIR / "gen-benchmark").glob("output*"):
        for mcp_dir in all_gen_mcp_dir.iterdir():
            if mcp_dir.is_dir():
                print(f"Setting up {mcp_dir.name}")
                mcp_tmp_dir = BENCH_DIR / mcp_dir.name / "repo"
                mcp_tmp_dir.mkdir(parents=True, exist_ok=True)
                proj_poc_dir = BENCH_DIR / mcp_dir.name / "poc"
                proj_poc_dir.mkdir(parents=True, exist_ok=True)
                shutil.copytree(mcp_dir, mcp_tmp_dir, dirs_exist_ok=True)
    return BENCH_DIR


def get_avail_port() -> int:
    while True:
        port = random.randint(1024, 65535)
        if port in PORT_SET:
            continue
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                PORT_SET.add(port)
                return port
        except OSError:
            continue


def get_unique_flag() -> str:
    while True:
        flag = "flag{" + str(uuid.uuid4()) + "}"
        if flag not in FLAG_MAP:
            return flag


def start_mcp_server(mcp_dir: Path, port: int):
    repo_dir = mcp_dir / "repo"
    current_env = os.environ.copy()
    current_env["COMPOSE_PROJECT_NAME"] = mcp_dir.name
    subprocess.run(
        ["sh", "startup.sh", str(port)],
        cwd=repo_dir,
        env=current_env,
    )
    with open(mcp_dir / "mcp_server_entry.json", "w") as f:
        json.dump(
            {
                "type": "streamable-http",
                "url": f"http://localhost:{port}/mcp",
            },
            f,
        )
    server_flag = get_unique_flag()
    FLAG_MAP[server_flag] = mcp_dir.name
    subprocess.run(
        ["docker", "compose", "exec", "-i", "mcp-server", "sh", "-c", f"echo {server_flag} > /flag"],
        cwd=repo_dir,
        env=current_env,
    )


def startup_flag_service(flag_service_dir: Path) -> int:
    flag_service_port = get_avail_port()
    current_env = os.environ.copy()
    current_env["FLAG_SERVICE_PORT"] = str(flag_service_port)
    with open(flag_service_dir / "all_server_flags.json", "w") as f:
        json.dump(FLAG_MAP, f)
    subprocess.run(
        ["docker", "compose", "up", "--build", "-d"],
        cwd=str(flag_service_dir),
        env=current_env,
    )
    return flag_service_port


def startup_internal_service(internal_service_dir: Path):
    current_env = os.environ.copy()
    internal_service_flag = get_unique_flag()
    current_env["INTERNAL_SERVICE_FLAG"] = internal_service_flag
    FLAG_MAP[internal_service_flag] = "internal-service"
    subprocess.run(
        ["docker", "compose", "up", "--build", "-d"],
        cwd=str(internal_service_dir),
        env=current_env,
    )


def shutdown_mcp_server(mcp_dir: Path):
    repo_dir = mcp_dir / "repo"
    current_env = os.environ.copy()
    current_env["COMPOSE_PROJECT_NAME"] = mcp_dir.name
    subprocess.run(
        ["sh", "shutdown.sh"],
        cwd=repo_dir,
        env=current_env,
    )


def operate_benchmark(bench_dir: str, action: Literal["startup", "cleanup"], max_workers: int = 10):
    bench_dir_path = Path(bench_dir)
    mcp_dirs = [mcp_dir for mcp_dir in bench_dir_path.iterdir() if mcp_dir.is_dir()]

    
    if action == "startup":
        operate_func = start_mcp_server
    elif action == "cleanup":
        operate_func = shutdown_mcp_server
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for mcp_dir in mcp_dirs:
            arg_list = [mcp_dir]
            if action == "startup":
                arg_list.append(get_avail_port())
            future = executor.submit(operate_func, *arg_list)
            futures.append(future)
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error {action} MCP server: {e}")

    if action == "startup":
        startup_internal_service(SERVICE_DIR / "internal-service")
        flag_service_port = startup_flag_service(SERVICE_DIR / "flag-service")
        with open(OUTPUT_DIR / "flag_service_url.txt", "w") as f:
            f.write(f"http://localhost:{str(flag_service_port)}/flag\n")
    if action == "cleanup":
        if bench_dir_path.exists():
            shutil.rmtree(bench_dir_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Setup or cleanup MCP benchmark servers")
    parser.add_argument("--bench-dir", type=str, default="/tmp/mcp-benchmark", help="Directory for benchmark setup")
    parser.add_argument("--max-workers", "-t", type=int, default=10, help="Maximum number of worker threads")
    parser.add_argument("action", default="setup", choices=["setup", "startup", "cleanup"], help="Action to perform: setup or cleanup")
    args = parser.parse_args()

    bench_dir = setup_bench_dir(args.bench_dir)
    if args.action == "startup":
        print(f"[*] Starting up benchmark servers in {bench_dir}")
        operate_benchmark(bench_dir, "startup", args.max_workers)
    elif args.action == "cleanup":
        print(f"[*] Cleaning up benchmark servers in {bench_dir}")
        operate_benchmark(bench_dir, "cleanup", args.max_workers)
