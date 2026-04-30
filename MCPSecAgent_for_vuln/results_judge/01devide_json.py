import multiprocessing
import os
import sys
import asyncio
from pathlib import Path
from tqdm import tqdm  
import json
from judge_agent import run_judge

# Generate three JSON files (update paths as needed)

def main():
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent  
    target_path = project_root / "results" / "rq1" / "semant_guard" 
    ltm_path = project_root / "results" / "ltm"

    repo_root = Path(__file__).resolve().parents[2] 

    # Vuln
    answer_path = repo_root / "MCPServerBenchmark/output/ground_truth.json"
    all_tool_path = repo_root / "MCPServerBenchmark/output/all_tool_info.json"

    
    if not target_path.exists():
        print(f"Error: directory does not exist: {target_path}")
        return

    json_files = list(target_path.glob("*.json"))
    
    if not json_files:
        print("No .json files found.")
        return

    print(f"Starting processing: {len(json_files)} files.")
    print(f"Target directory: {target_path}")

    for target_path in json_files:
        with open(target_path, 'r', encoding='utf-8') as f:
            target_content = f.read()
            target_data = json.loads(target_content)
        output_path1 = Path(__file__).resolve().parent / Path(target_path).parent.name / str(target_path.stem) / "target.json"
        output_path1.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path1, "w", encoding="utf-8") as f:
            json.dump(target_data, f, indent=4, ensure_ascii=False)

        
        
        with open(answer_path, 'r', encoding='utf-8') as f:
            answer_content = f.read()
            answer_data = json.loads(answer_content)
        output_path2 = Path(__file__).resolve().parent / Path(target_path).parent.name  / str(target_path.stem) / "answer.json"
        output_path2.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path2, "w", encoding="utf-8") as f:
            json.dump(answer_data[target_path.stem], f, indent=4, ensure_ascii=False)

        with open(all_tool_path, 'r', encoding='utf-8') as f:
            all_tool_content = f.read()
            all_tool_data = json.loads(all_tool_content)
        output_path3 = Path(__file__).resolve().parent / Path(target_path).parent.name / str(target_path.stem) / "all_tool.json"
        output_path3.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path3, "w", encoding="utf-8") as f:
            json.dump(all_tool_data[target_path.stem], f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    main()