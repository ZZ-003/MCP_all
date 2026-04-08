import json
from time import time
from os import getenv
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.messages import HumanMessage

from semant_guard.prompts.verify_agent import VERIFY_AGENT_PROMPT
from semant_guard.prompts import TASK_INSTRUCTION
from semant_guard.context.memory import LongTermMemory, ShortTermMemory
from semant_guard.context.utils import longterm_memory_to_markdown, shortterm_memory_to_markdown, vuln_info_to_markdown
from utils.utils import setup_log_dir
from utils.structured_output import get_structured_output_middleware
from utils.output_model import VerifiedVulnResponse

from dotenv import load_dotenv
load_dotenv()

class VerifyAgent():
    def __init__(self, project_dir: str, flag_service: str, ltm: LongTermMemory, all_tool_stm: dict[str, ShortTermMemory]):
        self.project_dir = project_dir
        self.llm = ChatOpenAI(
            model=getenv("VERIFY_AGENT_MODEL"),
            base_url=getenv("VERIFY_AGENT_BASE_URL"),
            api_key=getenv("VERIFY_AGENT_API_KEY"),
        )
        self.agent = create_deep_agent(
            model=self.llm,
            backend=FilesystemBackend(
                root_dir=project_dir,
                virtual_mode=True,
            ),
            middleware=[get_structured_output_middleware(VerifiedVulnResponse, self.llm)],
        )
        self.ltm = ltm
        self.all_tool_stm = all_tool_stm

    async def verify(self, vuln_info: dict, conn_info: dict) -> VerifiedVulnResponse:
        stm_markdown = "Tool Intent and Capability Analysis Memory\n\n"
        for tool_name, stm in self.all_tool_stm.items():
            stm_markdown += f"## Tool: {tool_name}\n"
            stm_markdown += shortterm_memory_to_markdown(stm) + "\n\n"

        prompt = ""
        prompt += f"## Connection Information: \n{json.dumps(conn_info, indent=2)}\n\n"
        prompt += vuln_info_to_markdown(vuln_info) + "\n\n"
        prompt += TASK_INSTRUCTION
        response = await self.agent.ainvoke({
            "messages": [
                HumanMessage(content=VERIFY_AGENT_PROMPT),
                HumanMessage(content=longterm_memory_to_markdown(self.ltm)),
                HumanMessage(content=stm_markdown),
                HumanMessage(content=prompt),
            ]
        })
        log_dir = setup_log_dir(self.project_dir, "verify_agent")
        with open(log_dir / f"{int(time())}.log", "w") as f:
            for msg in response["messages"]:
                f.write(msg.pretty_repr()+"\n")
                f.flush()
        return response["structured_response"]