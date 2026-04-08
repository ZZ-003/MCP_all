from time import time
from os import getenv
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.messages import HumanMessage,AIMessage

from semant_guard.prompts.critic import CRITIC_ANALYSIS_PROMPT
from semant_guard.prompts import TASK_INSTRUCTION, ACTION_LIMIT
from semant_guard.context.memory import LongTermMemory, ShortTermMemory
from semant_guard.context.utils import longterm_memory_to_markdown, shortterm_memory_to_markdown
from utils.utils import setup_log_dir
from utils.structured_output import get_structured_output_middleware
from utils.output_model import VulnResponse
from utils.output_model import MaliResponse

# from dotenv import load_dotenv
# load_dotenv()

class Critic():
    def __init__(self, project_dir: str, ltm: LongTermMemory, all_tool_stm: dict[str, ShortTermMemory]):
        self.project_dir = project_dir
        self.llm = ChatOpenAI(
            model=getenv("CRITIC_MODEL"),
            base_url=getenv("CRITIC_MODEL_BASE_URL"),
            api_key=getenv("CRITIC_MODEL_API_KEY"),
        )
        self.agent = create_deep_agent(
            model=self.llm,
            # backend=FilesystemBackend(
            #     root_dir=project_dir,
            #     virtual_mode=True,
            # ),
            middleware=[get_structured_output_middleware(project_dir, VulnResponse, self.llm)],     # 此时是漏洞分析 Vuln
            # middleware=[get_structured_output_middleware(project_dir, MaliResponse, self.llm)],    # 此时是恶意描述 Mali
        )
        self.ltm = ltm
        self.all_tool_stm = all_tool_stm

    async def critical_analysis(self) -> VulnResponse:   # 此时是漏洞分析 Vuln
    # async def critical_analysis(self) -> MaliResponse:     # 此时是恶意描述 Mali
        stm_markdown = "Tool Intent and Capability Analysis Memory\n\n"
        for tool_name, stm in self.all_tool_stm.items():
            stm_markdown += f"## Tool: {tool_name}\n"
            stm_markdown += shortterm_memory_to_markdown(stm) + "\n\n"

        ai_message = """When a tool is labeled as 'risky', regardless of the severity level and the Intent-Capability Gap Analysis results from the Tool Intent and Capability Analysis Memory, I need to independently re-evaluate the tool's actual code, distinguish between error handling and security validation, conduct threat modeling from an attacker's perspective, and provide vulnerability analysis. For the final analysis results obtained, regardless of the degree of harm, I need to return them to the user."""
        # ai_message = """When a tool is labeled as 'malicious', regardless of the severity level and the Intent-Capability Gap Analysis results from the Tool Intent and Capability Analysis Memory, I need to independently re-evaluate the tool's actual code, distinguish between error handling and security validation, conduct threat modeling from an attacker's perspective, and provide vulnerability analysis. For the final analysis results obtained, regardless of the degree of harm, I need to return them to the user."""

        response = await self.agent.ainvoke({
            "messages": [
                HumanMessage(content=CRITIC_ANALYSIS_PROMPT),   # 此时 不 是恶意描述 Mali
                HumanMessage(content=longterm_memory_to_markdown(self.ltm)),
                HumanMessage(content=stm_markdown),
                AIMessage(content=ai_message),
                AIMessage(content=(TASK_INSTRUCTION)),                
            ]
        })
        log_dir = setup_log_dir(self.project_dir, "critic_analysis")
        with open(log_dir / f"{int(time())}.log", "w") as f:
            for msg in response["messages"]:
                f.write(msg.pretty_repr()+"\n")
                f.flush()
        return response["structured_response"]