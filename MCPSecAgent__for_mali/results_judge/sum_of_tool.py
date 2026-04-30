import json
from pathlib import Path
from typing import Dict

# 四个实验目录
EXPERIMENT_DIRS = [
    "llm_only",
    "single_agent",
    "semant_guard",
    "scan_with_intent_capability",
]

# 需要统计的字段
STATS_FIELDS = [
    "True_Positive",
    "False_Positive",
    "False_Negative",
    "Correctly_identified_tools",
    "Incorrectly_identified_tools",
]


def calculate_statistics_for_dir(results_dir: Path) -> Dict:
    """统计单个目录下所有文件的工具数量"""
    json_files = list(results_dir.glob("*.json"))
    
    # 用于存储每个字段的工具数量
    stats = {field: 0 for field in STATS_FIELDS}
    files_processed = 0
    # 记录每个文件的 FP 和 FN 数量
    fp_fn_files = []
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            fp_count = len(data.get("False_Positive", []))
            fn_count = len(data.get("False_Negative", []))
            
            # 记录 FP>0 或 FN>0 的文件
            if fp_count > 0 or fn_count > 0:
                fp_fn_files.append({
                    "file_path": str(file_path.name),
                    "False_Positive": fp_count,
                    "False_Negative": fn_count,
                })
            
            for field in STATS_FIELDS:
                tools = data.get(field, [])
                if isinstance(tools, list):
                    stats[field] += len(tools)
            
            files_processed += 1
        except Exception as e:
            print(f"ERROR {file_path.name}: {e}")
    
    return {
        "dir_name": results_dir.name,
        "files_processed": files_processed,
        "stats": stats,
        "fp_fn_files": fp_fn_files,
    }


def print_directory_stats(data: Dict):
    """打印单个目录的统计结果"""
    print(f"\n{'='*60}")
    print(f"实验目录：{data['dir_name']}")
    print(f"{'='*60}")
    print(f"处理文件数：{data['files_processed']}")
    for field, count in data['stats'].items():
        print(f"{field}: {count}")
    
    # 打印 FP>0 或 FN>0 的文件
    if data.get("fp_fn_files"):
        print(f"\n--- FP>0 或 FN>0 的文件 ---")
        for file_info in data["fp_fn_files"]:
            print(f"  文件：{file_info['file_path']}")
            print(f"    False_Positive: {file_info['False_Positive']}")
            print(f"    False_Negative: {file_info['False_Negative']}")


def calculate_statistics():
    current_dir = Path(__file__).resolve().parent
    
    all_results = []
    
    # 总体统计
    overall_stats = {field: 0 for field in STATS_FIELDS}
    overall_files = 0
    
    for exp_dir in EXPERIMENT_DIRS:
        results_dir = current_dir / exp_dir
        if not results_dir.exists():
            print(f"\n[警告] 目录不存在：{results_dir}")
            continue
        
        dir_data = calculate_statistics_for_dir(results_dir)
        all_results.append(dir_data)
        print_directory_stats(dir_data)
        
        # 累加到总体统计
        overall_files += dir_data['files_processed']
        for field in STATS_FIELDS:
            overall_stats[field] += dir_data['stats'][field]
    
    # 打印汇总统计
    if all_results:
        print(f"\n{'='*60}")
        print("汇总统计 (所有实验)")
        print(f"{'='*60}")
        print(f"实验目录数：{len(all_results)}")
        print(f"总处理文件数：{overall_files}")
        print()
        for field, count in overall_stats.items():
            print(f"{field}: {count}")
        
        # 保存结果到 JSON 文件
        output_data = {
            "summary": {
                "total_experiments": len(all_results),
                "total_files": overall_files,
            },
            "by_experiment": all_results,
            "overall": overall_stats,
        }
        
        # 保存结果
        output_path = current_dir / "tool_statistics_result.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\n结果已保存到：{output_path}")


if __name__ == "__main__":
    calculate_statistics()
