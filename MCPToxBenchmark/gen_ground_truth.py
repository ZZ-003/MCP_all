import json
from pathlib import Path
import shutil


"""
Ground Truth Struct

{
    "[Project Name]" : {
        "[malicious_tool_name]" : [
            "[malicious_type_1]",
            "[malicious_type_2]",
            ...
            "[malicious_type_n]",
        ]
    },
    ...
}
"""


TOOL_MALICIOUS_MAP = {
    "write_file" : [
        "malicious",
    ],
    "simple_multiplication" : [
        "malicious",
    ],
    "list_directory" : [
        "malicious",
    ],
    "describe_table" : [
        "malicious",
    ],
    "log_injection_test" : [
        "malicious",
    ],
    "generate_image" : [
        "malicious",
    ],
    "put_schedules" : [
        "malicious",
    ],
    "git_checkout": [
        "malicious",
    ],
    "move_file": [
        "malicious",
    ],
    "send_email": [
        "malicious",
    ],
    "list_pull_requests": [
        "malicious",
    ],
}




def gen_server_ground_truth(malicious_tool_info_file: Path) -> dict:
    with open(malicious_tool_info_file, "r") as f:
        malicious_tool_info: dict = json.load(f)
    ground_truth: dict[str, list] = {}
    for _id, malicious_tool_list in malicious_tool_info.items():
        ground_truth[f"server{_id}_python"] = {}
        for malicious_tool in malicious_tool_list:
            malicious_types = TOOL_MALICIOUS_MAP.get(malicious_tool, [])
            ground_truth[f"server{_id}_python"][malicious_tool] = malicious_types
    return ground_truth

def gen_server_all_truth(all_tool_info_file: str) -> dict:
    with open(all_tool_info_file, "r") as f:
        all_tool_info: dict = json.load(f)
    all_truth: dict[str, list] = {}
    for _id, all_tool_list in all_tool_info.items():
        all_truth[f"server{_id}_python"] = all_tool_list
        # for all_tool in all_tool_list:
        #     # vuln_types = TOOL_VULN_MAP.get(vuln_tool, [])
        #     all_truth[f"server{_id}_python"] = all_tool
    return all_truth


if __name__ == "__main__":
    project_root = Path(__file__).parent
    output_dir = project_root / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    malicious_tool_info_file = project_root / "gen-benchmark" / "output_python" / "malicious_tool_info.json"
    server_ground_truth = gen_server_ground_truth(malicious_tool_info_file)
    full_ground_truth = {**server_ground_truth}
    with open(output_dir / "ground_truth.json", "w") as f:
        json.dump(full_ground_truth, f, indent=2)


    all_tool_info_path = project_root / "gen-benchmark" / "output_python" / "all_tool_info.json"
    all_tool_info = gen_server_all_truth(all_tool_info_path)
    # all_tool_truth = {**all_tool_info, **CUSTOM_ALL_TOOL}
    all_tool_truth = {**all_tool_info}
    with open(output_dir / "all_tool_info.json", "w") as f:
        json.dump(all_tool_truth, f, indent=2)
    