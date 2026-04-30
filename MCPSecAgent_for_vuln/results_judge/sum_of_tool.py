import json
from pathlib import Path
from typing import Dict

# Four experiment directories
EXPERIMENT_DIRS = [
    "llm_only",
    "single_agent",
    "semant_guard",
    "scan_with_intent_capability",
]

# Fields to be counted
STATS_FIELDS = [
    "True_Positive",
    "False_Positive",
    "False_Negative",
    "Correctly_identified_tools",
    "Incorrectly_identified_tools",
]


def calculate_statistics_for_dir(results_dir: Path) -> Dict:
    """Count tool occurrences across all files in a single directory."""
    json_files = list(results_dir.glob("*.json"))
    
    # Store tool counts for each field
    stats = {field: 0 for field in STATS_FIELDS}
    files_processed = 0
    # Track FP and FN counts per file
    fp_fn_files = []
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            fp_count = len(data.get("False_Positive", []))
            fn_count = len(data.get("False_Negative", []))
            
            # Record files where FP>0 or FN>0
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
    """Print statistics for a single directory."""
    print(f"\n{'='*60}")
    print(f"Experiment directory: {data['dir_name']}")
    print(f"{'='*60}")
    print(f"Files processed: {data['files_processed']}")
    for field, count in data['stats'].items():
        print(f"{field}: {count}")
    
    # Print files where FP>0 or FN>0
    if data.get("fp_fn_files"):
        print("\n--- Files with FP>0 or FN>0 ---")
        for file_info in data["fp_fn_files"]:
            print(f"  File: {file_info['file_path']}")
            print(f"    False_Positive: {file_info['False_Positive']}")
            print(f"    False_Negative: {file_info['False_Negative']}")


def calculate_statistics():
    current_dir = Path(__file__).resolve().parent
    
    all_results = []
    
    # Overall summary
    overall_stats = {field: 0 for field in STATS_FIELDS}
    overall_files = 0
    
    for exp_dir in EXPERIMENT_DIRS:
        results_dir = current_dir / exp_dir
        if not results_dir.exists():
            print(f"\n[Warning] Directory does not exist: {results_dir}")
            continue
        
        dir_data = calculate_statistics_for_dir(results_dir)
        all_results.append(dir_data)
        print_directory_stats(dir_data)
        
        # Add to overall summary
        overall_files += dir_data['files_processed']
        for field in STATS_FIELDS:
            overall_stats[field] += dir_data['stats'][field]
    
    # Print summary
    if all_results:
        print(f"\n{'='*60}")
        print("Summary statistics (all experiments)")
        print(f"{'='*60}")
        print(f"Number of experiment directories: {len(all_results)}")
        print(f"Total files processed: {overall_files}")
        print()
        for field, count in overall_stats.items():
            print(f"{field}: {count}")
        
        # Save results to a JSON file
        output_data = {
            "summary": {
                "total_experiments": len(all_results),
                "total_files": overall_files,
            },
            "by_experiment": all_results,
            "overall": overall_stats,
        }
        
        # Write output
        output_path = current_dir / "tool_statistics_result.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    calculate_statistics()
