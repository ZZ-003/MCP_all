import json
from pathlib import Path


def analyse_with_ground_truth(ground_truth_file: str, result_dir: str) -> dict:
    with open(ground_truth_file, "r") as f:
        ground_truth: dict = json.load(f)
    
    result_dir = Path(result_dir)
    scan_results = {}
    for file in result_dir.glob("*.json"):
        with open(file, "r") as f:
            scan_results[file.stem] = json.load(f)

    analyse_results = {}
    total_ture_vuln_count = 0
    total_positive_count = 0
    for server_id, true_vuln_list in ground_truth.items():
        total_ture_vuln_count += len(true_vuln_list)
        if server_id not in scan_results:
            analyse_results["no_scan_result"] = analyse_results.get("no_scan_result", 0) + 1
            continue
        try:
            positive_vuln_list = scan_results[server_id]["vulnerabilities"]
        except KeyError:
            print(server_id)
            raise
        server_positive_count = 0
        for tool_name, tag_list in true_vuln_list.items():
            true_positive = False
            for vuln_info in positive_vuln_list:
                for tag in tag_list:
                    if tool_name in vuln_info["tool_name"] and tag in vuln_info["type"]:
                        true_positive = True
                        break
                if true_positive:
                    break
            if true_positive:
                server_positive_count += 1
        if server_positive_count == 0:
            print(server_id)
        total_positive_count += server_positive_count
    analyse_results["total_ture_vuln_count"] = total_ture_vuln_count
    analyse_results["total_positive_count"] = total_positive_count
    analyse_results["precision"] = total_positive_count / total_ture_vuln_count if total_ture_vuln_count > 0 else 0
    return analyse_results

if __name__ == "__main__":
    project_dir = Path(__file__).parent.parent
    ground_truth_file = project_dir / "results/ground_truth.json"
    result_dir = project_dir / "results/llm_only_scan"
    results = analyse_with_ground_truth(ground_truth_file, result_dir)
    print(json.dumps(results, indent=2))