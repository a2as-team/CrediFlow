import asyncio
import sys
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
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
        ALWAYS use this Customer ID for any function parameter labeled 'cust_id' or 'customer_id'. 
        Do not ask the user for their ID if it is provided in the context. 
        The user will ask you queries related to banking, utilities, or deliveries. You have the following functions available:

        - fetch_details
        - RAG_query
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

        Follow these rules when responding:
        NOTE: 1. Use the Context Customer ID to call `fetch_details` or `transaction_details` first if you need to find specific loan_IDs or transaction_IDs.
        1. Carefully read the user's query and identify which function(s) are needed. Only use those functions.
        2. Map the user's request to the correct function parameters. Ask for missing parameters if necessary.
        3.Use customer_id as parameter. Don't ask for each and every parameter only important others are given in the tables.
        4. Generate a function call in JSON format with accurate parameter values.
        5. After calling the function, use the result to provide a helpful response to the user.

        Example flow:

        User: "I want to pay my electricity bill of $120 for account 12345."  
        Agent: 
    """
    ),
    tools=[get_toolcontext, RAG_query, bank_statement, bill_details, block_account, collection_alert, create_alert, delivery_status, emi_creation, emi_details, emi_pay, fetch_details, pay_bill, process_transaction, request_card, transaction_details
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
