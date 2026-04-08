import json
import shutil
from pathlib import Path
from random import choice, shuffle
from itertools import combinations

from mcp_python.benign_tools import BENIGN_TOOLS
from mcp_python.vuln_tools import VULN_TOOLS


ROOT_DIR = Path(__file__).parent
REPO_TMPL_DIR = ROOT_DIR / "repo_template_python"


PY_MCP_SERVER_SINGLE_FILE_TEMPLATE = """
from mcp.server.fastmcp import FastMCP
from typing import Optional, Dict, Any

mcp = FastMCP(name="{server_name}", host="0.0.0.0", port=8000)

[TOOLS]

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
"""


with open(REPO_TMPL_DIR / "Dockerfile", "r") as f:
    DOCKERFILE_TEMPLATE = f.read()


with open(REPO_TMPL_DIR / "requirements.txt", "r") as f:
    REQUIREMENTS_TEMPLATE = f.read()


server_name_list = [
    "NexusNode",
    "ContextFlow",
    "IrisLink",
    "JanusBridge",
    "DataForge MCP",
    "SyncQuarry",
    "AetherLine",
    "PrismGate",
    "SynapseStream",
    "DeepWell",
]


def split_tool_code(code: str):
    import_code, tool_code = code.split("@mcp.tool")
    tool_code = "@mcp.tool" + tool_code.strip()
    if "# ---SPLIT---" in code:
        import_code, tool_code = code.split("# ---SPLIT---")
    return import_code.strip(), tool_code.strip()


def gen_single_file(output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    vuln_tool_comb = combinations(VULN_TOOLS.items(), 2)
    benign_tool_comb = combinations(BENIGN_TOOLS.items(), 4)

    server_id = 0
    vuln_tool_info = {}
    all_tool_info = {}
    benign_tool_comb_list = list(benign_tool_comb)
    for vuln_tools in vuln_tool_comb:
        for benign_tools in benign_tool_comb_list:
            server_name = choice(server_name_list)
            server_code = PY_MCP_SERVER_SINGLE_FILE_TEMPLATE.format(server_name=server_name)
            tool_code_list = []
            import_code_set = set()
            vuln_tool_name_list = []
            all_tool_name_list = []
            for vuln_tool_name, vuln_tool_code in vuln_tools:
                vuln_tool_name_list.append(vuln_tool_name)
                all_tool_name_list.append(vuln_tool_name)
                import_code, tool_code = split_tool_code(vuln_tool_code)
                import_code_set.update(import_code.strip().split("\n"))
                tool_code_list.append(tool_code.strip())
            for benign_tool_name, benign_tool_code in benign_tools:
                all_tool_name_list.append(benign_tool_name)
                import_code, tool_code = split_tool_code(benign_tool_code)
                import_code_set.update(import_code.strip().split("\n"))
                tool_code_list.append(tool_code.strip())
            import_code_list = list(import_code_set)
            shuffle(import_code_list)
            shuffle(tool_code_list)
            server_code = '\n'.join(import_code_list) + "\n\n" + server_code
            server_code = server_code.replace("[TOOLS]", '\n\n'.join(tool_code_list))
            server_dir = output_dir / f"server{server_id}_python"
            server_dir.mkdir(exist_ok=True)
            with open(server_dir / "server.py", "w") as f:
                f.write(server_code)
            for file_path in REPO_TMPL_DIR.iterdir():
                if file_path.is_file():
                    target_file_path = server_dir / file_path.name
                    shutil.copy(file_path, target_file_path)
            vuln_tool_info[server_id] = vuln_tool_name_list
            all_tool_info[server_id] = all_tool_name_list
            server_id += 1
    with open(output_dir / "vuln_tool_info.json", "w") as f:
        json.dump(vuln_tool_info, f, indent=2)
    with open(output_dir / "all_tool_info.json", "w") as f:
        json.dump(all_tool_info, f, indent=2)

if __name__ == "__main__":
    output_dir = ROOT_DIR / "output_python"
    gen_single_file(str(output_dir))