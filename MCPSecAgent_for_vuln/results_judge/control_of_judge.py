import multiprocessing
import os
import sys
import asyncio
from pathlib import Path
from tqdm import tqdm  
from pathlib import Path
from judge_agent import run_judge


MAX_WORKERS = 3

def process_file_wrapper(args):
    target_file, answer_file, all_tool_path = args
    
    process_name = multiprocessing.current_process().name
    
    try:
        asyncio.run(run_judge(str(target_file), str(answer_file), str(all_tool_path)))
        return {"status": "success", "file": Path(target_file).name}
    except Exception as e:
        return {"status": "error", "file": Path(target_file).name, "error": str(e)}


def main():
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent  
    target_dir = project_root / "results" / "rq2" / "scan_with_intent_capability"

    repo_root = Path(__file__).resolve().parents[2] 

    # Vuln
    answer_path = repo_root / "MCPServerBenchmark/output/ground_truth.json"
    all_tool_path = repo_root / "MCPServerBenchmark/output/all_tool_info.json"

    # Mali
    # answer_path = repo_root / "MCPToxBenchmark/output/ground_truth.json"
    # all_tool_path = repo_root / "MCPToxBenchmark/output/all_tool_info.json"

    if not target_dir.exists():
        print(f"Error: directory does not exist: {target_dir}")
        return

    json_files = list(target_dir.glob("*.json"))
    
    if not json_files:
        print("No .json files found.")
        return

    print(f"Starting processing: {len(json_files)} files.")
    print(f"Target directory: {target_dir}")
    tasks = [(f, answer_path, all_tool_path) for f in json_files]
    results = []

    with multiprocessing.Pool(processes=MAX_WORKERS) as pool:
        iterator = pool.imap_unordered(process_file_wrapper, tasks, chunksize=1)
        for result in tqdm(iterator, total=len(tasks), desc="Processing"):
            results.append(result)


if __name__ == "__main__":
    main()