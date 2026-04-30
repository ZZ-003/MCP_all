import multiprocessing
import os
import sys
import asyncio
from pathlib import Path
from tqdm import tqdm  

from judge_agent import run_judge

# 加入 TN，需要换路径名

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
    # answer_path = "/home/ubuntu/mcp-sec/MCPServerBenchmark/output/ground_truth.json"   # 这是 Vuln 的答案
    # answer_path = "/home/ubuntu/mcp-sec/MCPToxBenchmark/output/ground_truth.json"  # 这是 Mali 的答案

    answer_path = "/home/zhong/AllCode/MCP_all/MCPServerBenchmark/output/ground_truth.json"   # 这是 Vuln 的答案
    all_tool_path = "/home/zhong/AllCode/MCP_all/MCPServerBenchmark/output/all_tool_info.json"  # 这是 Vuln 的答案

    # answer_path = "/home/zhong/AllCode/MCP_all/MCPToxBenchmark/output/ground_truth.json"   # 这是 Mali 的答案
    # all_tool_path = "/home/zhong/AllCode/MCP_all/MCPToxBenchmark/output/all_tool_info.json"  # 这是 Mali 的答案

    if not target_dir.exists():
        print(f"Error: 目录不存在 {target_dir}")
        return

    json_files = list(target_dir.glob("*.json"))
    
    if not json_files:
        print("未找到 .json 文件")
        return

    print(f"开始处理， {len(json_files)} 个文件。")
    print(f"目标目录: {target_dir}")
    tasks = [(f, answer_path, all_tool_path) for f in json_files]
    results = []

    # ctx = multiprocessing.get_context('spawn'); with ctx.Pool(...)
    with multiprocessing.Pool(processes=MAX_WORKERS) as pool:
        iterator = pool.imap_unordered(process_file_wrapper, tasks, chunksize=1)
        for result in tqdm(iterator, total=len(tasks), desc="Processing"):
            results.append(result)


if __name__ == "__main__":
    main()