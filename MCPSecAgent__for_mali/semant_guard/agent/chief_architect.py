from os import getenv
from time import time
from pathlib import Path
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.agents.structured_output import ToolStrategy
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage,AIMessage

from semant_guard.context.memory import LongTermMemory
from semant_guard.prompts.chief_architect import CHIEF_ARCHITECT_PROMPT
from semant_guard.prompts import TASK_INSTRUCTION, ACTION_LIMIT
from utils.structured_output import get_structured_output_middleware

from dotenv import load_dotenv
load_dotenv()


class ChiefArchitect:
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        llm = ChatOpenAI(
            model=getenv("CHIEF_ARCHITECT_MODEL"),
            base_url=getenv("CHIEF_ARCHITECT_MODEL_BASE_URL"),
            api_key=getenv("CHIEF_ARCHITECT_MODEL_API_KEY"),
            temperature=0,
        )

        self.agent = create_deep_agent(
            model=llm,
            backend=FilesystemBackend(
                root_dir=project_dir,
                virtual_mode=True,
            ),
            middleware=[get_structured_output_middleware(project_dir, LongTermMemory, llm)],
        )
        # Set up logging directory
        project_path = Path(project_dir)
        name = project_path.name
        while name == "repo":
            project_path = project_path.parent
            name = project_path.name
        self.log_dir = Path(__file__).parent.parent.parent / f"results/logs/chief_architect/{name}"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    async def analyze_repository(self) -> LongTermMemory:
        response = await self.agent.ainvoke(
            {
                "messages": [
                    HumanMessage(content=CHIEF_ARCHITECT_PROMPT),
                    # HumanMessage(content=ACTION_LIMIT),
                    # HumanMessage(content=TASK_INSTRUCTION),
                    AIMessage(content=ACTION_LIMIT),
                    AIMessage(content=TASK_INSTRUCTION + "For files with more than 100 lines, I need to use the `read_file` tool multiple times to read the file contents."),
                    # HumanMessage(content=ACTION_GUIDE),
                    
                ]
            }
        )
        with open(self.log_dir / f"chief_architect_analysis_{int(time())}.log", "w") as f:
            for msg in response["messages"]:
                f.write(msg.pretty_repr()+"\n")
                f.flush()
        print(response.keys())
        return response["structured_response"]