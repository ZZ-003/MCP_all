import json
from os import getenv
from time import time
from pathlib import Path
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage,AIMessage

from semant_guard.agent.chief_architect import ChiefArchitect
from semant_guard.context.utils import longterm_memory_to_markdown
from semant_guard.context.memory import LongTermMemory, ShortTermMemory

from utils.prompts import CODE_SCAN_PROMPT, MALICIOUS_TOOL_PROMPT
from utils.output_model import VulnResponse
from utils.output_model import MaliResponse
from utils.structured_output import get_structured_output_middleware
from utils.utils import setup_log_dir

from dotenv import load_dotenv
load_dotenv()

async def agent_with_ltm_scan(project_dir: str) -> dict:
    """
    Scan the given mcp server project directory for vulnerabilities using an agent with long-term memory.
    """
    chief_architect = ChiefArchitect(project_dir)
    ltm: LongTermMemory = await chief_architect.analyze_repository()
    parentfile_path = Path(__file__).resolve().parent
    server_name = Path(project_dir).parent.name
    ltm_path = parentfile_path.parent / "results" / "rq1" /  "semant_guard_ltm" / f"{server_name}.json"
    ltm_path.parent.mkdir(parents=True, exist_ok=True)
    with open(ltm_path,"w") as f:
        json.dump(ltm.model_dump(),f,indent=2)

    llm = ChatOpenAI(
        model=getenv("AGENT_WITH_LTM_MODEL"),
        base_url=getenv("AGENT_WITH_LTM_BASE_URL"),
        api_key=getenv("AGENT_WITH_LTM_API_KEY"),
        temperature=0,
    )
    agent = create_deep_agent(
        model=llm,
        backend=FilesystemBackend(
            root_dir=project_dir,
            virtual_mode=True,
        ),
        middleware=[
            get_structured_output_middleware(project_dir, VulnResponse, llm),
        ],
    )
    prompt = "I have been provided with global analysis information for this code repository. Now I can begin my task."
    response = await agent.ainvoke({
        "messages": [
            HumanMessage(content=CODE_SCAN_PROMPT),           
            HumanMessage(content=longterm_memory_to_markdown(ltm)),
            AIMessage(content=prompt),
        ]
    })
    log_dir = setup_log_dir(project_dir, "agent_with_ltm")
    log_file = f"{int(time())}.log"
    with open(log_dir / log_file, "w") as f:
        for msg in response['messages']:
            f.write(msg.pretty_repr() + "\n")
            f.flush()
    return response["structured_response"].model_dump()