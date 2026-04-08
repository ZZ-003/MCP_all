from os import getenv
from time import time
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_openai import ChatOpenAI
from langchain_qwq import ChatQwen

from utils.prompts import CODE_SCAN_PROMPT , All_CODE_SCAN_PROMPT , MALICIOUS_TOOL_PROMPT
from utils.output_model import VulnResponse, AllResponse
from utils.output_model import MaliResponse
from utils.structured_output import get_structured_output_middleware
from utils.utils import setup_log_dir

from dotenv import load_dotenv
load_dotenv()

async def single_agent_scan(project_dir: str) -> dict:
    llm = ChatOpenAI(
        model=getenv("SINGLE_AGENT_MODEL"),
        base_url=getenv("SINGLE_AGENT_BASE_URL"),
        api_key=getenv("SINGLE_AGENT_API_KEY"),
    )

    agent = create_deep_agent(
        model=llm,
        backend=FilesystemBackend(
            root_dir=project_dir,
            virtual_mode=True,
        ),
        middleware=[
            get_structured_output_middleware(project_dir, AllResponse, llm),
            # get_structured_output_middleware(project_dir, MaliResponse, llm),  # 此时是恶意描述 Mali
        ],
    )

    prompt = All_CODE_SCAN_PROMPT   # 此时是漏洞扫描的 prompt
    # prompt = MALICIOUS_TOOL_PROMPT    # 此时是恶意描述 Mali
    response = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})

    log_dir = setup_log_dir(project_dir, "single_agent")
    log_file = f"{int(time())}.log"
    with open(log_dir / log_file, "w") as f:
        for msg in response['messages']:
            f.write(msg.pretty_repr() + "\n")
            f.flush()
    return response["structured_response"].model_dump()