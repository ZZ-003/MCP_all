import json
from pathlib import Path
import shutil


"""
Ground Truth Struct

{
    "[Project Name]" : {
        "[vuln_tool_name]" : [
            "[vuln_type_1]",
            "[vuln_type_2]",
            ...
            "[vuln_type_n]",
        ]
    },
    ...
}
"""


TOOL_VULN_MAP = {
    "calculator": [
        "Remote Code Execution",
        "Code Execution",
        "RCE",
        "Code Injection",
    ],
    "view_log": [
        "Path Traversal",
    ],
    "write_todo": [
        "Path Traversal",
        "Arbitrary File Write",
    ],
    "git_execute": [
        "Command Injection",
    ],
    "download_file": [
        "Server Side Request Forgery",
        "Server-Side Request Forgery",
        "SSRF",
        "Path Traversal",
        "Arbitrary File Write",
    ],
}


CUSTOM_SERVER_GROUND_TRUTH = {
    "mcp-clickhouse": {
        "run_select_query": [
            "SQL Injection",
        ]
    },
    "mcp-doc-converter-python": {
        "convert_document": [
            "Command Injection",
        ],
        "convert_image": [
            "Command Injection",
        ],
    },
    "mcp-fetch-python": {
        "fetch_url": [
            "Server Side Request Forgery",
            "SSRF",
        ]
    },
    "mcp-filesystem-python": {
        "read_file": [
            "Path Traversal",
            "Arbitrary File Read",
        ],
        "write_file": [
            "Path Traversal",
            "Arbitrary File Write",
        ],
        "list_files": [
            "Path Traversal",
        ],
        },
    "mcp-mediawiki-server": {
        "search": [
            "Server-Side Request Forgery",
            "Improper Input Validation",
            "Allocation of Resources Without Limits or Throttling",
            "Missing Authorization"
        ],
        "get_page": [
            "Server-Side Request Forgery (SSRF)",
            "Path Traversal",
            "Improper Input Validation"
        ]
    },
    "mcp-ping-python": {
        "ping": [
        "Command Injection"
        ]
    },
    "mcp-sandbox": {
        "execute_code": [
        "Remote Code Execution",
        "Code Execution",
        "RCE"
        ]
    },
    "mcp-sql-optimizer": {},
    "mcp-polymarket": {
        "arbitrage_scan": [
            "Insufficient Input Validation"
        ],
        "research_market": [
            "Server-Side Request Forgery",
            "Information Exposure Through Unsanitized Output"
        ],
        "edge_finder": [
            "Server-Side Request Forgery",
            "Insecure Deserialization"
        ]
    },
    "mcp-sqlite": {
        "execute_sql": [
            "SQL Injection"
        ],
        "get_table_info": [
            "SQL Injection"
        ]
    },
    "mcp-Discord": {
        "send_message": [
            "Improper Input Validation",
            "Input Validation",
            "Privilege Escalation",
        ],
        "read_message": [
            "Improper Input Validation",
            "Input Validation",
            "Information Disclosure",
        ],
        "get_channel": [
            "Improper Input Validation",
            "Input Validation",
            "Information Disclosure"
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


"""NO_USE
    "mcp-5g": [
        "k8s_get_pods",
        "k8s_get_deployments",
        "k8s_get_services",
        "k8s_get_pod_logs",
        "k8s_describe_pod",
        "k8s_get_configmaps",
        "k8s_get_nodes",
        "k8s_get_events",
        "fiveg_core_topology",
        "fiveg_nf_status",
        "fiveg_slice_info",
        "fiveg_health_check"
    ],
    "mcp-appflowy": [
        "appflowy_login",
        "appflowy_refresh_token",
        "appflowy_list_workspaces",
        "appflowy_list_databases",
        "appflowy_get_database_fields",
        "appflowy_list_rows",
        "appflowy_get_row_details",
        "appflowy_create_row",
        "appflowy_upsert_row",
        "hello",
        "get_tasks",
        "add_task"
    ],
    "mcp-filesystem-server": [
        "read_file",
        "list_directory",
        "write_file",
        "create_directory",
        "delete_file",
        "delete_directory",
        "move_path",
        "get_file_info"
    ],
    "mcp-MariaDB": [
        "list_databases",
        "list_tables",
        "get_table_schema",
        "get_table_schema_with_relations",
        "execute_sql",
        "create_database",
        "create_vector_store",
        "list_vector_stores",
        "delete_vector_store",
        "insert_docs_vector_store",
        "search_vector_store"
    ],
"""

"""NO_USE
    "mcp-5g": {
        "k8s_get_pod_logs": [
        "Information Exposure Through Data Retrieval",
        "Uncontrolled Resource Consumption"
        ],
        "k8s_describe_pod": [
        "Information Exposure Through Sensitive Data Retrieval"
        ],
        "k8s_get_configmaps": [
        "Information Exposure Through Sensitive Data Retrieval"
        ],
        "k8s_get_events": [
        "Uncontrolled Resource Consumption"
        ],
        "k8s_get_nodes": [
        "Information Exposure Through Sensitive Data Retrieval"
        ],
        "k8s_get_services": [
        "Information Exposure Through Sensitive Data Retrieval"
        ],
        "k8s_get_deployments": [
        "Information Exposure Through Sensitive Data Retrieval"
        ],
        "fiveg_nf_status": [
        "Information Exposure Through Data Retrieval"
        ],
        "fiveg_slice_info": [
        "Information Exposure Through Sensitive Data Retrieval"
        ],
        "fiveg_health_check": [
        "Uncontrolled Resource Consumption",
        "Information Exposure Through Sensitive Data Retrieval"
        ],
        "fiveg_core_topology": [
        "Information Exposure Through Sensitive Data Retrieval"
        ],
        "http_transport": [
        "Authentication Bypass When Token Not Configured"
        ]
    },
    "mcp-appflowy": {
        "appflowy_login": [
            "Cleartext Transmission of Sensitive Information",
            "Insecure Credential Storage",
            "Information Exposure Through Error Messages"
        ],
        "appflowy_refresh_token": [
            "Insecure Token Storage",
            "Information Exposure Through Error Messages"
        ],
        "appflowy_list_workspaces": [
            "Information Exposure Through Error Messages"
        ],
        "appflowy_list_databases": [
            "Improper Input Validation",
            "Information Exposure Through Error Messages"
        ],
        "appflowy_get_database_fields": [
            "Improper Input Validation",
            "Information Exposure Through Error Messages"
        ],
        "appflowy_list_rows": [
            "Improper Input Validation",
            "Information Exposure Through Error Messages"
        ],
        "appflowy_get_row_details": [
            "Improper Input Validation",
            "Information Exposure Through Error Messages"
        ],
        "appflowy_create_row": [
            "Improper Input Validation",
            "Information Exposure Through Error Messages"
        ],
        "appflowy_upsert_row": [
            "Improper Input Validation",
            "Information Exposure Through Error Messages"
        ],
        "hello": [
            "Improper Output Neutralization for Logs"
        ],
        "get_tasks": [
            "Missing Authentication",
            "Use of Hard-coded Credentials"
        ],
        "add_task": [
            "Missing Authentication",
            "Use of Hard-coded Credentials"
        ],
        "global_issues": [
            "Insecure In-Memory Token Storage",
            "Improper Access Control"
        ]
    },
    "mcp-filesystem-server": {
        "read_file": [
            "Path Traversal",
            "Arbitrary File Read"
        ],
        "write_file": [
            "Path Traversal",
            "Arbitrary File Write"
        ],
        "list_directory": [
            "Path Traversal"
        ],
        "create_directory": [
            "Path Traversal"
        ],
        "delete_file": [
            "Path Traversal"
        ],
        "delete_directory": [
            "Path Traversal"
        ],
        "move_path": [
            "Path Traversal"
        ],
        "get_file_info": [
            "Path Traversal"
        ]
    },
    "mcp-MariaDB": {
        "execute_sql": [
            "SQL Injection",
            "SQL Command Injection"
        ],
        "create_database": [
            "SQL Injection"
        ],
        "create_vector_store": [
            "SQL Injection"
        ],
        "delete_vector_store": [
            "SQL Injection"
        ],
        "insert_docs_vector_store": [
            "SQL Injection"
        ],
        "list_tables": [
            "SQL Injection"
        ],
        "get_table_schema": [
            "SQL Injection"
        ],
        "get_table_schema_with_relations": [
            "SQL Injection"
        ],
        "list_vector_stores": [
            "SQL Injection"
        ],
        "search_vector_store": [
            "SQL Injection"
        ]
    },

"""


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
    