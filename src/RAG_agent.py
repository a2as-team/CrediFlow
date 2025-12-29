from google.adk.agents import Agent
from google.adk.tools import FunctionTool, ToolContext
from google.adk.tools.agent_tool import AgentTool
from tools import RAG_query


def get_toolcontext(tool_context: ToolContext, cust_id):
    tool_context.state["customer_id"] = cust_id


def get_query(query: str, tool_context: ToolContext):
    tool_context.state['query'] = query


rag_agent = Agent(
    name="RAG_agent",
    model="gemini-2.5-flash",
    description="A Retrieval-Augmented Generation agent for document analysis.",
    instruction="""
        You are a Retrieval-Augmented Generation (RAG) agent.
        Instructions:
        1. Invoke get_toolcontext to identify available to get cust_ID.
        2. Use get_query to know user query.
        3. Retrieve information strictly related to the query using the RAG_query(query) tool.
        4. Answer the user query only using retrieved content.
        5. Do not use external knowledge or assumptions.
        6. Keep the final answer concise, factual, and directly aligned with the query.
    """,
    tools=[get_toolcontext, get_query, RAG_query],
)

rag_agent_tool = AgentTool(agent=rag_agent)
