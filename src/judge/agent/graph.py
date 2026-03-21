from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from judge.agent.prompt import build_system_prompt
from judge.agent.tools import all_tools
from judge.llm.client import get_llm
from judge.models.pr import PRContext


def build_agent(pr: PRContext):
    llm = get_llm()
    llm_with_tools = llm.bind_tools(all_tools)
    system_prompt = build_system_prompt(pr)

    async def agent_node(state: MessagesState) -> dict:
        messages = [SystemMessage(content=system_prompt), *state["messages"]]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(all_tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")

    return graph.compile()


async def run_agent(pr: PRContext) -> str:
    agent = build_agent(pr)
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=f"Проверь PR #{pr.pr_number}")]},
    )
    return result["messages"][-1].content
