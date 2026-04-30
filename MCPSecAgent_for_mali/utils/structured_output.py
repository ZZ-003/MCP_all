from pathlib import Path
from time import time
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage
from langchain.agents import AgentState, create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.agents.middleware import after_agent


_DEFAULT_STRUCTURED_OUTPUT_INSTRUCTION = "Based on the previous analysis, provide structured output with tool."

def get_structured_output_middleware(project_dir:str,response_format, llm: ChatOpenAI, structured_output_instruction: str = _DEFAULT_STRUCTURED_OUTPUT_INSTRUCTION):
    @after_agent
    async def structured_output_middleware(state: AgentState, runtime):
        structured_output_agent = create_agent(
            model=llm,
            tools=[],
            response_format=ToolStrategy(response_format),
        )
        
        analysis_msg = state["messages"]
        messages = analysis_msg
    
        messages.append(HumanMessage(content=structured_output_instruction))
        

        project_path = Path(project_dir)
        name = project_path.name
        while name == "repo":
            project_path = project_path.parent
            name = project_path.name
        log_dir = Path(__file__).parent.parent / f"results/logs/chief_architect/messages/{name}"
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(time())
        with open(log_dir / f"message_{timestamp}.log", "w", encoding="utf-8") as f:
            for his_msg in messages:
                f.write(his_msg.pretty_repr()+ "\n")
            for state_msg in state["messages"]:
                f.write("All originally passed state information: \n" + state_msg.pretty_repr()+ "\n")
            f.write("Current second-to-last message:\n" + messages[-2].pretty_repr() + "\n")
            f.write("Current last message:\n" + messages[-1].pretty_repr() + "\n")
            f.flush()
        
        response = await structured_output_agent.ainvoke(
            {
                "messages": messages,
            }
        )
        return {"structured_response": response["structured_response"]}
    return structured_output_middleware