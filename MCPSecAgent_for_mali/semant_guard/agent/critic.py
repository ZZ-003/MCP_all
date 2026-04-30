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

from dotenv import load_dotenv
load_dotenv()

class Critic():
    def __init__(self, project_dir: str, ltm: LongTermMemory, all_tool_stm: dict[str, ShortTermMemory]):
        self.project_dir = project_dir
        self.llm = ChatOpenAI(
            model=getenv("CRITIC_MODEL"),
            base_url=getenv("CRITIC_MODEL_BASE_URL"),
            api_key=getenv("CRITIC_MODEL_API_KEY"),
            temperature=0,
        )
        self.agent = create_deep_agent(
            model=self.llm,
            middleware=[get_structured_output_middleware(project_dir, MaliResponse, self.llm)],   
        )
        self.ltm = ltm
        self.all_tool_stm = all_tool_stm

    async def critical_analysis(self) -> MaliResponse:    
        stm_markdown = "Tool Intent and Capability Analysis Memory\n\n"
        for tool_name, stm in self.all_tool_stm.items():
            stm_markdown += f"## Tool: {tool_name}\n"
            stm_markdown += shortterm_memory_to_markdown(stm) + "\n\n"

        ai_message = """When a tool is labeled as "malicious", I must independently re-evaluate the tool's actual code, regardless of its severity level or the Intent-Capability Gap Analysis results stored in the Tool Intent and Capability Analysis Memory. I must not conclude that the code is harmless simply because the executable portion of the code is empty. I must return the final analysis results to the user regardless of the level of harm identified."""

        response = await self.agent.ainvoke({
            "messages": [
                HumanMessage(content=CRITIC_ANALYSIS_PROMPT),  
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