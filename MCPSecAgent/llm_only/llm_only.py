import time
from os import getenv, walk
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

from utils.output_model import VulnResponse, AllResponse, MaliResponse
from utils.prompts import CODE_SCAN_PROMPT , All_CODE_SCAN_PROMPT , MALICIOUS_TOOL_PROMPT
from utils.utils import setup_log_dir

# from dotenv import load_dotenv
# load_dotenv()

async def llm_only_scan(project_dir: str) -> dict:
    project_path = Path(project_dir)

    if getenv("LLM_ONLY_MODEL") is None:
        raise ValueError("Please set LLM_ONLY_MODEL environment variable for llm-only scan.")
    llm = ChatOpenAI(
        model=getenv("LLM_ONLY_MODEL"),
        base_url=getenv("LLM_ONLY_BASE_URL"),
        api_key=getenv("LLM_ONLY_API_KEY"),
    )
    agent = create_agent(
        model=llm,
        tools=[],
        response_format=ToolStrategy(AllResponse)  # 此时是漏洞分析 Vuln
        # response_format=ToolStrategy(MaliResponse)  # 此时是恶意描述 Mali
    )

    # 需要跳过的目录和文件
    skip_dirs = {'.git', '__pycache__', 'node_modules', '.venv'}
    skip_files = {
        "startup.sh", "shutdown.sh", "docker-compose.yml", "pyproject.toml"
        ".gitignore", "uv.lock", ".dockerignore", ".DS_Store","RAEDME.md"
    }
        
    # 收集所有代码文件内容
    all_files_content = []
    file_count = 0
    
    for dirpath, dirnames, filenames in walk(project_path):
        # 过滤要跳过的目录，避免递归进入
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        
        # print(project_path)
        if dirpath.split('/')[-1] in skip_dirs:
            continue
        
        for filename in filenames:
            if filename in skip_files:
                continue
            file_path = Path(dirpath) / filename
            
            try:
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    relative_path = file_path.relative_to(project_path)
                    # print(relative_path)
                    all_files_content.append(f"=== File: {relative_path} ===\n{content}\n")
                    file_count += 1
            except Exception as e:
                # 跳过无法读取的文件
                print(f"Warning: Could not read {file_path}: {e}")
                continue
    
    # 构建LLM prompt
    files_text = "\n\n".join(all_files_content)

    prompt = All_CODE_SCAN_PROMPT      # 此时是漏洞分析 Vuln
    # prompt = MALICIOUS_TOOL_PROMPT   # 此时是恶意描述 Mali

    prompt += f"## Codebase ({file_count} files):\n"
    prompt += files_text
    
    response = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})

    log_dir = setup_log_dir(str(project_dir), "llm_only")
    log_file = log_dir / f"{int(time.time())}.log"
    with open(log_file, 'w', encoding='utf-8') as f:
        for msg in response['messages']:
            f.write(msg.pretty_repr() + "\n")
            f.flush()

    return response["structured_response"].model_dump()

