import json
from pathlib import Path
import shutil


"""
Ground Truth Struct

{
    "[Project Name]" : {
        "[vuln_tool_name]" : [
            "[CWE-xxx]",
            "[CWE-xxx]",
            ...
            "[CWE-xxx]",
        ]
    },
    ...
}
"""


TOOL_VULN_MAP = {
    "calculator": [
        "CWE-94",
        "CWE-95",
    ],
    "view_log": [
        "CWE-22",
    ],
    "write_todo": [
        "CWE-22",
        "CWE-73",
    ],
    "git_execute": [
        "CWE-78",
    ],
    "download_file": [
        "CWE-918",
        "CWE-22",
        "CWE-73",
    ],
}


CUSTOM_SERVER_GROUND_TRUTH = {
    "mcp-clickhouse": {
        "run_select_query": [
            "CWE-89",
        ]
    },
    "mcp-doc-converter-python": {
        "convert_document": [
            "CWE-78",
        ],
        "convert_image": [
            "CWE-78",
        ],
    },
    "mcp-fetch-python": {
        "fetch_url": [
            "CWE-918",
        ]
    },
    "mcp-filesystem-python": {
        "read_file": [
            "CWE-22",
        ],
        "write_file": [
            "CWE-22",
            "CWE-73",
        ],
        "list_files": [
            "CWE-22",
        ],
        },
    "mcp-mediawiki-server": {
        "search": [
            "CWE-918",
            "CWE-20",
            "CWE-770",
            "CWE-862"
        ],
        "get_page": [
            "CWE-918",
            "CWE-22",
            "CWE-20"
        ]
    },
    "mcp-ping-python": {
        "ping": [
        "CWE-78"
        ]
    },
    "mcp-sandbox": {
        "execute_code": [
        "CWE-94",
        "CWE-95",
        ]
    },
    "mcp-sql-optimizer": {},
    "mcp-polymarket": {
        "arbitrage_scan": [
            "CWE-20"
        ],
        "research_market": [
            "CWE-918",
            "CWE-200"
        ],
        "edge_finder": [
            "CWE-918",
            "CWE-502"
        ]
    },
    "mcp-sqlite": {
        "execute_sql": [
            "CWE-89"
        ],
        "get_table_info": [
            "CWE-89"
        ]
    },
    "mcp-Discord": {
        "send_message": [
            "CWE-20",
            "CWE-269",
            "CWE-306",
            "CWE-770",
        ],
        "read_message": [
            "CWE-20",
            "CWE-200",
            "CWE-862",
            "CWE-359",
        ],
        "get_channel": [
            "CWE-20",
            "CWE-200",
            "CWE-215",
        ]
    }
}


CUSTOM_ALL_TOOL = {
    "mcp-clickhouse": [
        "list_databases",
        "list_tables",
        "run_select_query",
        "run_chdb_select_query"
    ],
    "mcp-doc-converter-python": [
        "convert_document",
        "convert_image"
    ],
    "mcp-fetch-python": [
        "fetch_url"
    ],
    "mcp-filesystem-python": [
        "read_file",
        "write_file",
        "list_files"
    ],
    "mcp-mediawiki-server": [
        "search",
        "get_page"
    ],
    "mcp-ping-python": [
        "ping"
    ],
    "mcp-sandbox": [
        "execute_code"
    ],
    "mcp-sql-optimizer": [
        "analyze_query",
        "optimize_query",
        "suggest_indexes"
    ],
    "mcp-polymarket": [
        "search_markets",
        "get_market",
        "trending_markets",
        "calculate_ev",
        "kelly_size",
        "arbitrage_scan",
        "market_summary",
        "research_market",
        "edge_finder"
    ],
    "mcp-sqlite": [
        "execute_sql",
        "get_table_info"
    ],
    "mcp-Discord": [
        "send_message",
        "read_message",
        "get_channel"
    ]
}


def gen_server_ground_truth(vuln_tool_info_file: str) -> dict:
    with open(vuln_tool_info_file, "r") as f:
        vuln_tool_info: dict = json.load(f)
    ground_truth: dict[str, list] = {}
    for _id, vuln_tool_list in vuln_tool_info.items():
        ground_truth[f"server{_id}_python"] = {}
        for vuln_tool in vuln_tool_list:
            vuln_types = TOOL_VULN_MAP.get(vuln_tool, [])
            ground_truth[f"server{_id}_python"][vuln_tool] = vuln_types
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
    vuln_tool_info_file = project_root / "gen-benchmark" / "output_python" / "vuln_tool_info.json"
    server_ground_truth = gen_server_ground_truth(vuln_tool_info_file)
    full_ground_truth = {**server_ground_truth, **CUSTOM_SERVER_GROUND_TRUTH}
    with open(output_dir / "ground_truth.json", "w") as f:
        json.dump(full_ground_truth, f, indent=2)
    
    all_tool_info_path = project_root / "gen-benchmark" / "output_python" / "all_tool_info.json"
    all_tool_info = gen_server_all_truth(all_tool_info_path)

    all_tool_truth = {**all_tool_info, **CUSTOM_ALL_TOOL}

    with open(output_dir / "all_tool_info.json", "w") as f:
        json.dump(all_tool_truth, f, indent=2)
    # dst_path = output_dir / "all_tool_info.json"
    # shutil.copy(src_path, dst_path)