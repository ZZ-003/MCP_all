import json
from time import time
from os import getenv
from pathlib import Path
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.messages import HumanMessage,AIMessage

from semant_guard.prompts.taint_sleuths import *
from semant_guard.prompts import TASK_INSTRUCTION, ACTION_LIMIT
from semant_guard.tools.python_tool import get_python_tool
from semant_guard.context.memory import LongTermMemory, AllToolSTM
from semant_guard.context.utils import longterm_memory_to_markdown, shortterm_memory_to_markdown
from utils.utils import setup_log_dir
from utils.structured_output import get_structured_output_middleware

from dotenv import load_dotenv
load_dotenv()

class TaintSleuths:
    def __init__(self, project_dir: str, ltm: LongTermMemory):
        self.project_dir = project_dir
        self.llm = ChatOpenAI(
            model=getenv("TAINT_SLEUTHS_MODEL"),
            base_url=getenv("TAINT_SLEUTHS_MODEL_BASE_URL"),
            api_key=getenv("TAINT_SLEUTHS_MODEL_API_KEY"),
            temperature=0,
        )
        self.agent = create_deep_agent(
            model=self.llm,
            backend=FilesystemBackend(
                root_dir=project_dir,
                virtual_mode=True,
            ),
            middleware=[get_structured_output_middleware(project_dir, AllToolSTM, self.llm)], # 此时是漏洞分析 Vuln，不是 恶意分析
        )
        self.ltm = ltm


    async def intent_capability_static_analysis(self, tools: dict[str, str]) -> AllToolSTM:
        prompt = "Analyze the following tools:\n"
        for tool_name, tool_desc in tools.items():
            tool_def = f"Tool Name: {tool_name}\n"
            tool_def += f"Tool Description: {tool_desc}\n"
            
            prompt += tool_def + "\n"

        ADD_LIMIT = """For each identified tool, I need to examine the discrepancy between its 'intent and capability' across the complete code workflow. A clear distinction must be made between error handling and security validation; the presence of error handling mechanisms does not equate to code security. I should use the STRIDE or CWE taxonomy for systematic security analysis. If any tool is flagged as risky, regardless of the severity level, I need to report it."""        
        response = await self.agent.ainvoke({
            "messages": [
                HumanMessage(content=INTENT_CAPABILITY_STATIC_ANALYSIS_PROMPT),  # 此时是漏洞分析 Vuln，不是 恶意分析
                HumanMessage(content=longterm_memory_to_markdown(self.ltm)),
                HumanMessage(content=prompt),
                AIMessage(content=(ACTION_LIMIT + ADD_LIMIT + TASK_INSTRUCTION)),  # 漏洞分析用
                # AIMessage(content=(ACTION_LIMIT + "For each identified tool that appears in the 'Long Term Memory of this MCP Server Project', I need to use read_file to read the corresponding code for analysis." + TASK_INSTRUCTION)),  # 恶意描述检测用 Mali
            ]
        })
        log_dir = setup_log_dir(self.project_dir, "taint_sleuths_static")
        with open(log_dir / f"{int(time())}.log", "w") as f:
            for msg in response["messages"]:
                f.write(msg.pretty_repr()+"\n")
                f.flush()
        print(response.keys())
        return response["structured_response"]

    async def intent_capability_dynamic_verify(self, tool_name: str, tool_desc: str, work_dir: str, conn_info: dict) -> AllToolSTM:
        # work_dir is reserved for saving temporary PoC python scripts during dynamic analysis
        self.agent_with_py_tool = create_deep_agent(
            model=self.llm,
            backend=FilesystemBackend(
                root_dir=self.project_dir,
                virtual_mode=True,
            ),
            tools=[get_python_tool(work_dir)],
            middleware=[get_structured_output_middleware(self.project_dir, AllToolSTM, self.llm)],
        )

        tool_def = f"Tool Name: {tool_name}\n"
        tool_def += f"Tool Description: {tool_desc}\n\n"
        prompt = tool_def
        prompt += f"## Connection Information: \n{json.dumps(conn_info, indent=2)}\n\n{TASK_INSTRUCTION}"
        response = await self.agent_with_py_tool.ainvoke({
            "messages": [
                HumanMessage(content=INTENT_CAPABILITY_DYNAMIC_ANALYSIS_PROMPT),
                HumanMessage(content=longterm_memory_to_markdown(self.ltm)),
                HumanMessage(content=prompt),
            ]
        })
        log_dir = setup_log_dir(self.project_dir, "taint_sleuths_dynamic")
        with open(log_dir / f"{tool_name}_{int(time())}.log", "w") as f:
            for msg in response["messages"]:
                f.write(msg.pretty_repr()+"\n")
                f.flush()
        return response["structured_response"]