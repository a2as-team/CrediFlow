import streamlit as st
import asyncio
from google.genai import types
from google.adk.runners import Runner
from agent import call_agent_async, root_agent, APP_NAME, session_service
from tools import login, signup, make_con

# Page Configuration
st.set_page_config(
    page_title="CrediFlow",
    layout="centered"
)

# Dark Theme CSS (No Emojis)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Global Dark Theme */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    
    /* Logo Container */
    .logo-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        background-color: #161b22;
        border-radius: 12px;
        margin-bottom: 2rem;
        border: 1px solid #30363d;
    }
    
    .logo-text {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #4da6ff, #00ffff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -1px;
    }
    
    .tagline {
        color: #8b949e;
        font-size: 0.9rem;
        margin-top: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 600;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input {
        background-color: #0d1117;
        color: #c9d1d9;
        border: 1px solid #30363d;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #0e1117;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #8b949e;
    }
    
    .stTabs [aria-selected="true"] {
        color: #58a6ff !important;
        border-bottom-color: #58a6ff !important;
    }

    /* Primary Buttons */
    div.stButton > button:first-child {
        background-color: #238636;
        color: white;
        border: 1px solid rgba(240, 246, 252, 0.1);
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-weight: 600;
        width: 100%;
        transition: 0.2s;
    }
    
    div.stButton > button:first-child:hover {
        background-color: #2ea043;
        border-color: #8b949e;
    }

    /* Logout Button */
    div.logout-btn > button:first-child {
        background-color: #da3633 !important;
        border: 1px solid #da3633 !important;
    }
    div.logout-btn > button:first-child:hover {
        background-color: #b62324 !important;
    }

    /* Chat Messages */
    .stChatMessage {
        background-color: #161b22;
        border: 1px solid #30363d;
    }
</style>
""", unsafe_allow_html=True)

# --- State Initialization ---
if "cust_id" not in st.session_state:
    st.session_state.cust_id = None
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "runner" not in st.session_state:
    st.session_state.runner = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Async Helper ---


def run_async(coroutine):
    """Executes async coroutines in a synchronous context"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coroutine)

# --- Synchronous Authentication Logic ---


def process_login(username, password):
    """Synchronous login handler"""
    if not username or not password:
        return False, "Please fill in all fields."

    if login(username, password):
        cust_id = username
        try:
            existing_sessions = run_async(
                session_service.list_sessions(app_name=APP_NAME, user_id=cust_id))

            if existing_sessions and existing_sessions.sessions:
                session_id = existing_sessions.sessions[0].id
            else:
                new_session = run_async(session_service.create_session(
                    app_name=APP_NAME, user_id=cust_id))
                session_id = new_session.id

            runner = Runner(agent=root_agent, app_name=APP_NAME,
                            session_service=session_service)
            return True, (cust_id, session_id, runner)
        except Exception as e:
            return False, f"Session Error: {str(e)}"

    return False, "Invalid credentials."


def process_signup(name, phone, email, password):
    """Synchronous signup handler"""
    if not all([name, phone, email, password]):
        return False, "Please fill in all fields."

    # Standard synchronous signup
    if signup(name, phone, email, password):
        try:
            cursor_cust, cursor_trans, cursor_del, cursor_emi, conn_cust, conn_del, conn_trans, conn_emi = make_con()
            cursor_cust.execute(
                "SELECT customer_id FROM customer_logins WHERE email=?", (email,))
            row = cursor_cust.fetchone()

            if row:
                cust_id = row[0]
                new_session = run_async(session_service.create_session(
                    app_name=APP_NAME, user_id=cust_id))
                session_id = new_session.id

                runner = Runner(agent=root_agent, app_name=APP_NAME,
                                session_service=session_service)
                return True, (cust_id, session_id, runner)
        except Exception as e:
            return False, f"Session Error: {str(e)}"

    return False, "Email already registered or error occurred."

# --- Async Agent Response (ONLY Async Function) ---


async def get_agent_response(user_input):
    """Asynchronous agent interaction"""
    content = types.Content(role="user", parts=[types.Part(
        text=f"Current Customer ID: {st.session_state.cust_id}\nUser Query: \"{user_input}\""
    )])
    # This remains async as requested
    response = await call_agent_async(st.session_state.runner, st.session_state.cust_id, st.session_state.session_id, content)
    return response

# --- UI Components ---

# Minimalist Text Logo
st.markdown("""
    <div class="logo-container">
        <h1 class="logo-text">CrediFlow</h1>
        <p class="tagline">Intelligent Banking Assistant</p>
    </div>
""", unsafe_allow_html=True)

if not st.session_state.cust_id:
    # Auth Tabs
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        st.subheader("Welcome Back")
        with st.form("login_form"):
            user_in = st.text_input(
                "Customer ID", placeholder="e.g. CUST12345")
            pass_in = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Access Account")

            if submit_login:
                with st.spinner("Authenticating..."):
                    # Direct Synchronous Call
                    success, result = process_login(user_in, pass_in)
                    if success:
                        st.session_state.cust_id, st.session_state.session_id, st.session_state.runner = result
                        st.rerun()
                    else:
                        st.error(result)

    with tab2:
        st.subheader("Create Account")
        with st.form("signup_form"):
            s_name = st.text_input("Full Name")
            s_phone = st.text_input("Phone Number")
            s_email = st.text_input("Email Address")
            s_pass = st.text_input("Password", type="password")
            submit_signup = st.form_submit_button("Register Now")

            if submit_signup:
                with st.spinner("Creating account..."):
                    # Direct Synchronous Call
                    success, result = process_signup(
                        s_name, s_phone, s_email, s_pass)
                    if success:
                        st.session_state.cust_id, st.session_state.session_id, st.session_state.runner = result
                        st.success(f"Account created! ID: {result[0]}")
                        st.rerun()
                    else:
                        st.error(result)

else:
    # Sidebar
    with st.sidebar:
        st.header("Dashboard")
        st.markdown(f"**Logged in as:**\n`{st.session_state.cust_id}`")
        st.caption(f"Session: {st.session_state.session_id[:8]}...")

        st.divider()

        st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
        if st.button("Sign Out"):
            st.session_state.clear()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Chat Interface
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Type your banking query here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                # Run the only async function via helper
                response_text = run_async(get_agent_response(prompt))
                st.markdown(response_text)

        st.session_state.messages.append(
            {"role": "assistant", "content": response_text})
