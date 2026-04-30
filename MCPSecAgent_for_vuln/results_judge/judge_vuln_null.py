import json
import os
from pathlib import Path


def load_json_file(file_path: str) -> dict | list:
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_metrics(target_data: dict, subfolder_path: Path) -> dict:
    """Check items where the 'type' field is empty in 'vulnerabilities'."""
    vulnerabilities = target_data.get('vulnerabilities', [])
    null_type_count = 0
    null_type_items = []
    
    for vuln in vulnerabilities:
        tool_name = vuln.get('tool_name', '')
        vuln_type = vuln.get('type', '')
        
        if not vuln_type:  
            null_type_count += 1
            null_type_items.append({
                'tool_name': tool_name,
                'vuln_type': vuln_type,
                'full_vuln': vuln
            })
    
    if null_type_count > 0:
        print(f"  [Warning] {subfolder_path.name}: found {null_type_count} vulnerabilities with empty vuln_type")
        for item in null_type_items:
            print(f"    - tool_name: {item['tool_name']}, type: '{item['vuln_type']}'")
    
    return {
        'null_type_count': null_type_count,
        'null_type_items': null_type_items
    }



def process_subfolder(subfolder_path: Path) -> None:
    """Process a single subfolder and compute metrics."""
    target_path = subfolder_path / 'target.json'
    if not target_path.exists():
        print(f"  [Skip] {subfolder_path.name}: missing target.json")
        return
    target_data = load_json_file(target_path)
    metrics = calculate_metrics(target_data, subfolder_path)
     

def main():
    EXPERIMENT_DIRS = [
        "llm_only",
        "single_agent",
        "semant_guard",
        "scan_with_intent_capability",
    ]

    for exp_dir in EXPERIMENT_DIRS:
        base_dir = Path(__file__).parent / exp_dir

        
        if not base_dir.exists():
            print(f"Error: directory does not exist - {base_dir}")
            continue
        
        print(f"Starting directory: {base_dir}")
        print("-" * 60)

        subfolders = [d for d in base_dir.iterdir() if d.is_dir()]

        print(f"Found {len(subfolders)} subfolders")
        print("-" * 60)
        
        for subfolder in sorted(subfolders):
            process_subfolder(subfolder)
    


if __name__ == '__main__':
    main()
