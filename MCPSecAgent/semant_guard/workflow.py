import json
from pathlib import Path
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from semant_guard.agent.chief_architect import ChiefArchitect
from semant_guard.agent.taint_sleuths import TaintSleuths
from semant_guard.agent.critic import Critic
from semant_guard.context.memory import LongTermMemory, ShortTermMemory


async def static_scan_benchmark(project_dir: str) -> dict:
    """
    Orchestrates the scanning of a code repository for vulnerabilities or malicious descriptions
    using the Chief Architect and Taint Sleuths agents.
    """    
    # build long-term memory using Chief Architect
    chief_architect = ChiefArchitect(project_dir)
    ltm: LongTermMemory = await chief_architect.analyze_repository()

    parentfile_path = Path(__file__).resolve().parent
    server_name = Path(project_dir).parent.name
    ltm_path = parentfile_path.parent / "results" / "rq2" /"ltm" / f"{server_name}.json"
    ltm_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ltm_path,"w") as f:
        json.dump(ltm.model_dump(),f,indent=2)


    taint_sleuths = TaintSleuths(project_dir, ltm)
    
    tool_stm: dict[str, ShortTermMemory] = {}
    tools: dict[str, str] = {}
    for tool in ltm.mcp_tools:
        tool_name = tool.name
        tool_desc = tool.description
        tools[tool_name] = tool_desc

    tool_stms_response = await taint_sleuths.intent_capability_static_analysis(tools)
    tool_stm = tool_stms_response.ShortTermMemories

    stm_path = parentfile_path.parent / "results" / "rq2" /"stm" / f"{server_name}.json"
    stm_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stm_path,"w") as f:
        json.dump(tool_stms_response.model_dump(), f, indent=2)
    
    critic = Critic(project_dir, ltm, tool_stm)
    # vuln_report = await critic.critical_analysis()
    # return vuln_report.model_dump()
    mali_report = await critic.critical_analysis()
    return mali_report.model_dump()


# async def dynamic_scan_benchmark(bench_dir: str) -> list[dict]:
#     vuln_report_list = []
#     bench_path = Path(bench_dir)
#     repo_dir = bench_path / "repo"
#     poc_dir = bench_path / "poc"

#     # build long-term memory using Chief Architect
#     chief_architect = ChiefArchitect(str(repo_dir))
#     ltm: LongTermMemory = await chief_architect.analyze_repository()

#     taint_sleuths = TaintSleuths(str(repo_dir), str(poc_dir), ltm)
#     tool_stm: dict[str, ShortTermMemory] = {}
#     with open(bench_path / "mcp_server_entry.json", "r") as f:
#         conn_info = json.load(f)
#     assert "streamable-http" == conn_info["type"]
#     async with streamablehttp_client(conn_info["url"]) as (
#         read_stream,
#         write_stream,
#         _,
#     ):
#         # Create a session using the client streams
#         async with ClientSession(read_stream, write_stream) as session:
#             # Initialize the connection
#             await session.initialize()
#             # List available tools
#             tools = await session.list_tools()
#             for tool in tools.tools:
#                 stm = await taint_sleuths.intent_capability_static_analysis(
#                     tool.name, tool.description
#                 )
#                 tool_stm[tool.name] = stm
#                 vuln_report = await taint_sleuths.intent_capability_dynamic_verify(conn_info)
#                 vuln_report_list.append(vuln_report.model_dump())    
#     return vuln_report_list