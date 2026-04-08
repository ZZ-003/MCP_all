import json
from pathlib import Path
from typing import Dict, List

# 四个实验目录
EXPERIMENT_DIRS = [
    "llm_only",
    "single_agent",
    "semant_guard",
    "scan_with_intent_capability",
]

# 统计结果

def calculate_statistics_for_dir(results_dir: Path) -> Dict:
    """统计单个目录的结果"""
    json_files = list(results_dir.glob("**/result.json"))
    
    stats = {
        "dir_name": results_dir.name,
        "files_count": len(json_files),
        "True_Positive": 0,
        "False_Positive": 0,
        "False_Negative": 0,
        "servers_processed": 0,
        "Correctly_identified_tools_Num": 0,
        "Incorrectly_identified_tools_Num": 0,
        "tp_files": [],
        "fp_files": [],
        "fn_files": [],  # 记录 FN != 0 的文件
        "cn_files" :[],  # 记录 CN != 6 的文件
        "in_files": [],  # 记录 IN > 0 的文件
        "errors": [],
    }
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            TP = data.get("True_Positive_Num", 0)
            FP = data.get("False_Positive_Num", 0)
            FN = data.get("False_Negative_Num", 0)
            CN = data.get("Correctly_identified_tools_Num", 0)
            IN = data.get('Incorrectly_identified_tools_Num', 0)
            
            # 记录异常文件
            if TP != 2:
                stats["tp_files"].append((file_path.parent.name, TP))
            if FP != 0:
                stats["fp_files"].append((file_path.parent.name, FP))
            if FN != 0:
                stats["fn_files"].append((file_path.parent.name, FN))
            if CN != 6:
                stats["cn_files"].append((file_path.parent.name, CN))
            if IN > 0:
                stats["in_files"].append((file_path.parent.name, IN))
            
            # 累加统计
            stats["True_Positive"] += TP
            stats["False_Positive"] += FP
            stats["False_Negative"] += FN
            stats["servers_processed"] += 1
            stats["Correctly_identified_tools_Num"] += CN
            stats["Incorrectly_identified_tools_Num"] += IN

        except Exception as e:
            stats["errors"].append((file_path.parent.name, str(e)))
    
    return stats


def print_directory_stats(stats: Dict):
    """打印单个目录的统计结果"""
    print(f"\n{'='*60}")
    print(f"实验目录：{stats['dir_name']}")
    print(f"{'='*60}")
    print(f"{'处理文件数':<20}: {stats['files_count']}")
    print(f"{'Total Servers':<20}: {stats['servers_processed']}")
    print(f"{'Total Tools (Vuln/Mali)':<20}: 100")
    print(f"{'True_Positive_Num':<20}: {stats['True_Positive']}")
    print(f"{'False_Positive_Num':<20}: {stats['False_Positive']}")
    print(f"{'False_Negative_Num':<20}: {stats['False_Negative']}")
    print(f"{'Correctly_identified_tools':<20}: {stats['Correctly_identified_tools_Num']}")
    print(f"{'Incorrectly_identified_tools':<20}: {stats['Incorrectly_identified_tools_Num']}")
    
    if stats['tp_files']:
        print(f"\n  [TP != 2] ({len(stats['tp_files'])} 个):")
        for fname, tp in stats['tp_files']:
            print(f"    - {fname}: TP={tp}")

    if stats['fp_files']:
        print(f"\n  [FP != 0] ({len(stats['fp_files'])} 个):")
        for fname, fn in stats['fp_files']:
            print(f"    - {fname}: FP={fn}")

    if stats['fn_files']:
        print(f"\n  [FN != 0] ({len(stats['fn_files'])} 个):")
        for fname, fn in stats['fn_files']:
            print(f"    - {fname}: FN={fn}")
    
    if stats['cn_files']:
        print(f"\n  [CN != 6] ({len(stats['cn_files'])} 个):")
        for fname, cn in stats['cn_files']:
            print(f"    - {fname}: CN={cn}")

    if stats['in_files']:
        print(f"\n  [IN > 0] ({len(stats['in_files'])} 个):")
        for fname, in_val in stats['in_files']:
            print(f"    - {fname}: IN={in_val}")
    
    if stats['errors']:
        print(f"\n  [ERRORS] ({len(stats['errors'])} 个):")
        for fname, err in stats['errors']:
            print(f"    - {fname}: {err}")


def calculate_statistics():
    current_dir = Path(__file__).resolve().parent
    
    all_stats = []
    
    for exp_dir in EXPERIMENT_DIRS:
        results_dir = current_dir / exp_dir
        if not results_dir.exists():
            print(f"\n[警告] 目录不存在：{results_dir}")
            continue
        
        stats = calculate_statistics_for_dir(results_dir)
        all_stats.append(stats)
        print_directory_stats(stats)
    
    if all_stats:

        print(f"\n{'='*60}")
        print(f"{'目录':<25} | {'TP':>5} | {'FP':>5} | {'FN':>5} | {'CN':>5} | {'IN':>5}")
        print(f"{'-'*60}")
        for s in all_stats:
            tp = s['True_Positive']
            fp = s['False_Positive']
            fn = s['False_Negative']
            cn = s['Correctly_identified_tools_Num']
            In = s['Incorrectly_identified_tools_Num']
            print(f"{s['dir_name']:<25} | {tp:>5} | {fp:>5} | {fn:>5} | {cn:>5} | {In:>5}")


if __name__ == "__main__":
    calculate_statistics()
