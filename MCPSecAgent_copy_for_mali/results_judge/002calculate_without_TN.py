import json
import os
from pathlib import Path

#初步统计 result.json,这会刷新结果，要依次跑遍03

def load_json_file(file_path: str) -> dict | list:
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_target_tools_with_types(target_data: dict) -> dict[str, list[str]]:
    tool_types = {}
    # vulnerabilities = target_data.get('vulnerabilities', [])
    vulnerabilities = target_data.get('Maliciousness', [])
    for vuln in vulnerabilities:
        tool_name = vuln.get('tool_name', '')
        vuln_type = vuln.get('type', '')
        
        if tool_name not in tool_types:
            tool_types[tool_name] = []
        
        if vuln_type and vuln_type not in tool_types[tool_name]:
            tool_types[tool_name].append(vuln_type)
    
    return tool_types


def calculate_metrics(all_tools: list, answer_data: dict, target_data: dict) -> dict:
    target_tool_types = get_target_tools_with_types(target_data)
    target_tools_set = set(target_tool_types.keys())
    all_tools_set = set(all_tools)
    answer_tools_set = set(answer_data.keys())
    
    true_positive_num = 0
    false_positive_num = 0
    for tool in all_tools_set:  ############# 还要加上 当 vuln_type 不为空，才算误报
        if tool in target_tools_set and tool not in answer_tools_set:
            false_positive_num += 1
    
    false_negative_num = 0
    for tool in all_tools_set:
        if tool in answer_tools_set:
            if tool not in target_tools_set:
                # 在 answer 中但不在 target 中
                false_negative_num += 1
            elif not target_tool_types.get(tool, []):
                # 在 target 中但 type 为空   #####################  "" / '' 也算空？
                false_negative_num += 1
    
    correctly_identified_tools_num = 0
    for tool in target_tools_set:
        if tool in all_tools_set:
            correctly_identified_tools_num += 1
    
    incorrectly_identified_tools_num = 0
    for tool in target_tools_set:
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
    """处理单个子文件夹，计算指标并保存结果"""
    all_tool_path = subfolder_path / 'all_tool.json'
    answer_path = subfolder_path / 'answer.json'
    target_path = subfolder_path / 'target.json'
    result_path = subfolder_path / 'result.json'
    
    if not all_tool_path.exists():
        print(f"  [跳过] {subfolder_path.name}: 缺少 all_tool.json")
        return
    if not answer_path.exists():
        print(f"  [跳过] {subfolder_path.name}: 缺少 answer.json")
        return
    if not target_path.exists():
        print(f"  [跳过] {subfolder_path.name}: 缺少 target.json")
        return
    all_tools = load_json_file(all_tool_path)
    answer_data = load_json_file(answer_path)
    target_data = load_json_file(target_path)
    
    metrics = calculate_metrics(all_tools, answer_data, target_data)
    
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
            print(f"错误：目录不存在 - {base_dir}")
            continue
        
        print(f"开始处理目录：{base_dir}")
        print("-" * 60)
        subfolders = [d for d in base_dir.iterdir() if d.is_dir()]
        print(f"找到 {len(subfolders)} 个子文件夹")
        print("-" * 60)
        
        for subfolder in sorted(subfolders):
            process_subfolder(subfolder)
    


if __name__ == '__main__':
    main()
