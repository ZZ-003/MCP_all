from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage
from langchain.agents import AgentState, create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.agents.middleware import after_agent


def get_structured_output_middleware(response_format, llm: ChatOpenAI):
    @after_agent
    def structured_output_middleware(state: AgentState, runtime):
        structured_output_agent = create_agent(
            model=llm,
            tools=[],
            response_format=ToolStrategy(response_format),
        )
        messages = state["messages"]
        messages.append(HumanMessage(content="Based on the previous analysis, structured output will be provided."))
        response = structured_output_agent.invoke(
            {
                "messages": messages,
            }
        )
        return {"structured_response": response["structured_response"]}
    return structured_output_middleware