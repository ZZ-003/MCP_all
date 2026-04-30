import json
import os
from pathlib import Path

def load_json_file(file_path: str) -> dict | list:
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_target_tools_with_types(target_data: dict) -> dict[str, list[str]]:
    tool_types = {}
    vulnerabilities = target_data.get('vulnerabilities', [])
    maliciousness = target_data.get('Maliciousness', [])
    all_vulnerabilities = vulnerabilities + maliciousness
    
    for vuln in all_vulnerabilities:
        tool_name = vuln.get('tool_name', '')
        vuln_type = vuln.get('type', '')
        
        if tool_name not in tool_types:
            tool_types[tool_name] = []
        
        if vuln_type and vuln_type not in tool_types[tool_name]:
            tool_types[tool_name].append(vuln_type)
    
    return tool_types

def get_ltm_tools(ltm_data:dict):
    return {tool['name'] for tool in ltm_data.get('mcp_tools', [])}


def calculate_metrics(all_tools: list, answer_data: dict, target_data: dict,ltm_data:dict) -> dict:
    target_tool_types = get_target_tools_with_types(target_data)
    target_tools_set = set(target_tool_types.keys())
    all_tools_set = set(all_tools)
    answer_tools_set = set(answer_data.keys())
    ltm_tools_set = get_ltm_tools(ltm_data) if ltm_data else None
    
    true_positive_num = 0
    for tool in all_tools_set:
        if tool in target_tools_set and tool in answer_tools_set:
            target_vuln_types = target_tool_types.get(tool, [])
            answer_vuln_types = answer_data.get(tool, [])
            
            found_match = False
            for target_type in target_vuln_types:
                for answer_type in answer_vuln_types:
                    if target_type == answer_type:
                        true_positive_num += 1
                        found_match = True
                        break
                if found_match:
                    break
    
    false_positive_num = 0
    for tool in all_tools_set:  
        if tool in target_tools_set and target_tool_types[tool] != ["None"] and tool not in answer_tools_set:            
            false_positive_num += 1
    
    false_negative_num = 0
    for tool in all_tools_set:
        if tool in answer_tools_set:
            if tool not in target_tools_set:
                false_negative_num += 1
            elif not target_tool_types.get(tool, []):
                false_negative_num += 1
            elif target_tool_types.get(tool, []) == ["None"]:
                false_negative_num += 1

    
    correctly_identified_tools_num = 0
    for tool in target_tools_set if ltm_data is None else ltm_tools_set:
        if tool in all_tools_set:
            correctly_identified_tools_num += 1
    
    incorrectly_identified_tools_num = 0
    for tool in target_tools_set if ltm_data is None else ltm_tools_set:
        if tool not in all_tools_set:
            incorrectly_identified_tools_num += 1
    
    return {
        "True_Positive_Num": true_positive_num,
        "False_Positive_Num": false_positive_num,
        "False_Negative_Num": false_negative_num,
        "Correctly_identified_tools_Num": correctly_identified_tools_num,
        "Incorrectly_identified_tools_Num": incorrectly_identified_tools_num
    }


def process_subfolder(subfolder_path: Path) -> None:
    """Process a single subfolder, compute metrics, and save results."""
    all_tool_path = subfolder_path / 'all_tool.json'
    answer_path = subfolder_path / 'answer.json'
    target_path = subfolder_path / 'target.json'
    result_path = subfolder_path / 'result.json'

    parentfile_path = Path(__file__).resolve().parent
    if subfolder_path.parent.name == "scan_with_intent_capability":
        ltm_path = parentfile_path.parent / "results" / "rq2" /  "ltm" / f"{subfolder_path.name}.json"
    elif subfolder_path.parent.name == "semant_guard":
        ltm_path = parentfile_path.parent / "results" / "rq1" /  "semant_guard_ltm" / f"{subfolder_path.name}.json"
    else:
        ltm_path = None
    
    if not all_tool_path.exists():
        print(f"  [Skip] {subfolder_path.name}: missing all_tool.json")
        return
    if not answer_path.exists():
        print(f"  [Skip] {subfolder_path.name}: missing answer.json")
        return
    if not target_path.exists():
        print(f"  [Skip] {subfolder_path.name}: missing target.json")
        return
    all_tools = load_json_file(all_tool_path)
    answer_data = load_json_file(answer_path)
    target_data = load_json_file(target_path)
    ltm_data = load_json_file(ltm_path) if ltm_path else None
    if (ltm_data == [] or ltm_data =={} or ltm_data ==None) and ltm_path is not None:
        print(f"  [Warning] {subfolder_path.name}: LTM data is empty; this may affect evaluation results.")
    
    metrics = calculate_metrics(all_tools, answer_data, target_data,ltm_data)
    
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=4, ensure_ascii=False)
    

def main():
    EXPERIMENT_DIRS = [
        "llm_only",
        "single_agent",
        "semant_guard",
        "scan_with_intent_capability",
    ]

    for exp_dir in EXPERIMENT_DIRS:
        base_dir = Path(__file__).parent / exp_dir

        # base_dir = Path(__file__).parent / 'scan_with_intent_capability'
        
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
