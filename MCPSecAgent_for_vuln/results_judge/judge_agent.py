from pathlib import Path
from time import time
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain.agents.structured_output import ToolStrategy
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

import logging
import asyncio
import json
from pydantic import BaseModel, Field

from prompt import PROMPT

class ANSWER(BaseModel):
    True_Positive_Num: int = Field(description="The number of vulnerable tools correctly identified as vulnerable.")


class JudgeAgent:
    def __init__(self, project_dir: str , answer_dir:str, all_tool_path:str):
        self.project_dir = project_dir
        self.project_path = Path(project_dir)
        self.answer_path = Path(answer_dir)
        self.all_tool_path = Path(all_tool_path)

        self.agent = create_deep_agent(
            model=ChatOpenAI(
            ),
            response_format=ToolStrategy(ANSWER),
        )


    async def analyze_repository(self) -> ANSWER:
        with open(self.project_path, 'r', encoding='utf-8') as f:
            project_content = f.read()
            project_data = json.loads(project_content)
        
        with open(self.answer_path, 'r', encoding='utf-8') as f:
            answer_content = f.read()
            answer_data = json.loads(answer_content)

        with open(self.all_tool_path, 'r', encoding='utf-8') as f:
            all_tool_content = f.read()
            all_tool_data = json.loads(all_tool_content)
        formatted_prompt = PROMPT.format(
            target_content=json.dumps(project_data, ensure_ascii=False, indent=2),
            answer_content=json.dumps(answer_data[self.project_path.stem], ensure_ascii=False, indent=2),
            all_tool_content=json.dumps(all_tool_data[self.project_path.stem], ensure_ascii=False, indent=2)
        )

        try:
            response = await self.agent.ainvoke(
                {
                    "messages": [
                        HumanMessage(content=formatted_prompt),
                        AIMessage(content="I need to inform the user about my analysis process, and now I will start my task and analysis."),
                    ]
                }
            )

            output_key = "structured_response"
            if output_key not in response and "structured_output" in response:
                output_key = "structured_output"
            if output_key not in response:
                logging.error(f"Agent response missing '{output_key}': {response.keys()}")
                raise ValueError(f"Agent did not produce structured output. Available keys: {list(response.keys())}")
            log_path = Path(__file__).resolve().parent / "log" / self.project_path.parent.name / self.project_path.stem / f"{int(time())}.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "w") as f:
                for msg in response["messages"]:
                    f.write(msg.pretty_repr()+"\n")
                    f.flush()            
            
            return response[output_key]
        except Exception as e:
            logging.error(f"Error in agent invocation: {e}")
            raise


async def run_judge(target_dir , answer_dir, all_tool_path):
    judge_agent = JudgeAgent(target_dir , answer_dir, all_tool_path)
    result: ANSWER = await judge_agent.analyze_repository()
    try:
        result_data = result.model_dump()
    except AttributeError:
        result_data = result.dict()


    TN_num = result_data["True_Positive_Num"]
    output_path = Path(__file__).resolve().parent / Path(target_dir).parent.name / Path(target_dir).stem  / "result.json"

    print(output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'r', encoding='utf-8') as f:
        content = json.load(f)
    with open(output_path, 'w', encoding='utf-8') as f:
        content["True_Positive_Num"] = TN_num
        json.dump(content, f, indent=4, ensure_ascii=False)