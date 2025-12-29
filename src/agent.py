import asyncio
import sys
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from RAG_agent import rag_agent_tool
from google.adk.agents import Agent
from google.adk.tools import ToolContext
from tools import RAG_query, bank_statement, bill_details, block_account, collection_alert, create_alert, delivery_status, emi_creation, emi_details, emi_pay, fetch_details, pay_bill, process_transaction, request_card, transaction_details

load_dotenv()
session_service = InMemorySessionService()


def get_toolcontext(tool_context: ToolContext, cust_id):
    tool_context.state["customer_id"] = cust_id


root_agent = Agent(
    name="Banking_helper_agent",
    model="gemini-2.5-flash",
    description=(
        """
        This agent is a helpful assistant that can perform banking and utility-related actions for the user. It can:
        Fetch account details, bank statements, and transaction history.
        Pay bills, create alerts, and manage collections.
        Handle EMI creation, details, and payments.
        Block accounts, request cards, and check delivery status.
        The agent uses the functions provided to execute user requests accurately and securely, only calling the relevant functions mentioned in the user's query
    """
    ),
    instruction=(
        """
        You are a smart banking assistant.

        CRITICAL RULE:
        The "Current Customer ID" will be provided in the context of every message.
        ALWAYS use this Customer ID for any function parameter labeled "cust_id" or "customer_id".
        Do NOT ask the user for their customer ID if it is already provided.

        The user may ask queries related to banking, utilities, or deliveries.

        AVAILABLE FUNCTIONS:
        - fetch_details
        - rag_agent_tool
        - bank_statement
        - bill_details
        - block_account
        - collection_alert
        - create_alert
        - delivery_status
        - emi_creation
        - emi_details
        - emi_pay
        - pay_bill
        - process_transaction
        - request_card
        - transaction_details

        RESPONSE RULES:
        1. Carefully understand the user query.
        2. If the user asks/requires document-based, policy-based, or contextual understanding, FIRST call `rag_agent_tool`.
        3. Use `fetch_details` or `transaction_details` FIRST if loan_id, bill_id, or transaction_id is required and not explicitly provided.
        4. Only call the function(s) necessary for the request.
        5. Use `customer_id` exactly as provided in the context.
        6. Ask the user only for critical missing parameters.
        7. Generate function calls strictly in valid JSON.
        8. Use the function response to produce a clear and concise final answer.

    """
    ),
    tools=[get_toolcontext, rag_agent_tool, bank_statement, bill_details, block_account, collection_alert, create_alert, delivery_status, emi_creation, emi_details, emi_pay, fetch_details, pay_bill, process_transaction, request_card, transaction_details
           ],
)

APP_NAME = "CrediFlow"


async def call_agent_async(runner, USER_ID, SESSION_ID, content):
    final_text_response = None
    try:
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text and not part.text.isspace():
                            final_text_response = part.text.strip()

    except Exception as e:
        return f"**Error:** {str(e)}"

    if not final_text_response:
        final_text_response = "No final response returned by the agent."
    return f"{final_text_response}"


async def main_async():
    # --- 1. LOGIN / SESSION INITIALIZATION (Done once) ---
    try:
        USER_ID = input("Enter your name to Login: ").strip()
        if not USER_ID:
            print("User ID cannot be empty.")
            return
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        return

    # Check for existing session or create a new one
    existing_sessions = await session_service.list_sessions(
        app_name=APP_NAME,
        user_id=USER_ID,
    )

    if existing_sessions and len(existing_sessions.sessions) > 0:
        SESSION_ID = existing_sessions.sessions[0].id
        print(f"Resumed existing session: {SESSION_ID}", file=sys.stderr)
    else:
        new_session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
        )
        SESSION_ID = new_session.id
        print(f"Created new session: {SESSION_ID}", file=sys.stderr)

    # Initialize Runner
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    query = input(f"\n{USER_ID}: ")
    print("...Agent is thinking...", file=sys.stderr)

    user_prompt = f"""User Query: "{query}" """
    content = types.Content(
        role="user",
        parts=[types.Part(text=user_prompt)],
    )

    # Call Agent with the SAME Session ID
    final_response_string = await call_agent_async(
        runner, USER_ID, SESSION_ID, content
    )
    print(f"Agent: {final_response_string}")

if __name__ == "__main__":
    asyncio.run(main_async())
