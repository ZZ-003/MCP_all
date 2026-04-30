import json
import os
from pathlib import Path

#查看又饿米有vuln_type为空

def load_json_file(file_path: str) -> dict | list:
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_metrics(target_data: dict, subfolder_path: Path) -> dict:
    """检查 vulnerabilities 中 type 字段为空的项"""
    vulnerabilities = target_data.get('vulnerabilities', [])
    null_type_count = 0
    null_type_items = []
    
    for vuln in vulnerabilities:
        tool_name = vuln.get('tool_name', '')
        vuln_type = vuln.get('type', '')
        
        if not vuln_type:  # 捕获空字符串、None、缺失字段
            null_type_count += 1
            null_type_items.append({
                'tool_name': tool_name,
                'vuln_type': vuln_type,
                'full_vuln': vuln
            })
    
    # 打印统计信息
    if null_type_count > 0:
        print(f"  [警告] {subfolder_path.name}: 发现 {null_type_count} 个 vuln_type 为空的漏洞")
        for item in null_type_items:
            print(f"    - tool_name: {item['tool_name']}, type: '{item['vuln_type']}'")
    
    return {
        'null_type_count': null_type_count,
        'null_type_items': null_type_items
    }



def process_subfolder(subfolder_path: Path) -> None:
    """处理单个子文件夹，计算指标并保存结果"""
    target_path = subfolder_path / 'target.json'
    if not target_path.exists():
        print(f"  [跳过] {subfolder_path.name}: 缺少 target.json")
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
