import streamlit as st
import requests
import json
import os
from pathlib import Path

# ============================================
# PAGE CONFIG (Must be first Streamlit command)
# ============================================
st.set_page_config(page_title="Enterprise SLM", page_icon="🤖", layout="wide")

API_URL = "http://127.0.0.1:8000"

# ============================================
# SESSION FILE - Bulletproof path using pathlib
# ============================================
# frontend/app.py -> go up one level to project root -> data/.session
SESSION_FILE = str(Path(__file__).resolve().parent.parent / "data" / ".session")

def save_session(token: str, username: str) -> None:
    try:
        Path(SESSION_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(SESSION_FILE, "w") as f:
            json.dump({"token": token, "username": username}, f)
    except Exception as e:
        print(f"[SESSION] Failed to save: {e}")

def load_session():
    try:
        if Path(SESSION_FILE).exists():
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)
                token = data.get("token")
                username = data.get("username")
                if token and username:
                    return token, username
    except Exception as e:
        print(f"[SESSION] Failed to load: {e}")
    return None, None

def clear_session():
    try:
        if Path(SESSION_FILE).exists():
            os.remove(SESSION_FILE)
    except Exception:
        pass

# ============================================
# RESTORE SESSION ON EVERY PAGE LOAD
# ============================================
if "token" not in st.session_state:
    saved_token, saved_username = load_session()
    if saved_token and saved_username:
        try:
            test = requests.get(
                f"{API_URL}/history/",
                headers={"Authorization": f"Bearer {saved_token}"},
                timeout=5
            )
            if test.status_code == 200:
                st.session_state["token"] = saved_token
                st.session_state["username"] = saved_username
            else:
                clear_session()
        except Exception:
            clear_session()

# ============================================
# GLOBAL CSS
# ============================================
st.markdown(
    """
    <style>
        /* Remove default top padding */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0 !important;
        }
        
        /* Remove ALL container borders */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
        }
        
        /* Remove form borders */
        [data-testid="stForm"] {
            border: none !important;
            padding: 0 !important;
        }
        
        /* Round the input box */
        [data-testid="stForm"] [data-testid="stTextInput"] input {
            border-radius: 20px;
            padding: 12px 20px;
            border: 1px solid #444;
        }
        
        /* Remove the Streamlit header bar */
        header[data-testid="stHeader"] {
            display: none !important;
        }
        
        /* Remove the deploy button */
        [data-testid="stToolbar"] {
            display: none !important;
        }
        
        /* Fix sidebar header alignment */
        [data-testid="stSidebar"] {
            padding-top: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================
# HELPERS
# ============================================
def get_headers():
    return {"Authorization": f"Bearer {st.session_state['token']}"}

def init_state():
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "conversation_id" not in st.session_state:
        st.session_state["conversation_id"] = None

# ============================================
# LOGIN SCREEN
# ============================================
def show_login():
    st.markdown("")
    st.markdown("")
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.title("🔒 Enterprise AI Portal")
        st.markdown("Please log in with your employee credentials.")

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In", use_container_width=True)

            if submitted:
                try:
                    response = requests.post(
                        f"{API_URL}/auth/login",
                        json={"username": username, "password": password}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state["token"] = data["access_token"]
                        st.session_state["username"] = username
                        st.session_state["messages"] = []
                        st.session_state["conversation_id"] = None
                        save_session(data["access_token"], username)
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to server. Is FastAPI running?")

# ============================================
# LEFT SIDEBAR
# ============================================
def show_left_sidebar():
    with st.sidebar:
        st.markdown("## 💬 Chats")
        
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state["messages"] = []
            st.session_state["conversation_id"] = None
            st.rerun()
        
        st.divider()
        
        try:
            response = requests.get(
                f"{API_URL}/history/",
                headers=get_headers(),
                timeout=10
            )
            if response.status_code == 200:
                conversations = response.json()
                if not conversations:
                    st.caption("No past chats yet.")
                for conv in conversations:
                    label = f"📁 {conv['title']}"
                    if st.session_state.get("conversation_id") == conv["id"]:
                        label = f"▶️ {conv['title']}"
                    
                    if st.button(label, key=f"conv_{conv['id']}", use_container_width=True):
                        load_conversation(conv["id"])
        except Exception:
            st.caption("Could not load history.")

# ============================================
# LOAD PAST CONVERSATION
# ============================================
def load_conversation(conv_id: int):
    response = requests.get(
        f"{API_URL}/history/{conv_id}",
        headers=get_headers(),
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        st.session_state["conversation_id"] = conv_id
        st.session_state["messages"] = []
        
        for msg in data["messages"]:
            if msg["role"] == "user":
                st.session_state["messages"].append({
                    "role": "user",
                    "content": msg["content"]
                })
            else:
                try:
                    parsed = json.loads(msg["content"])
                    st.session_state["messages"].append({
                        "role": "assistant",
                        "code": parsed.get("code", ""),
                        "explanation": parsed.get("explanation", ""),
                        "review_notes": parsed.get("review_notes", "")
                    })
                except Exception:
                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": msg["content"]
                    })
        st.rerun()

# ============================================
# LOGOUT
# ============================================
def do_logout():
    try:
        requests.post(
            f"{API_URL}/auth/logout",
            json={"token": st.session_state["token"]}
        )
    except Exception:
        pass
    clear_session()
    st.session_state.clear()
    st.rerun()

# ============================================
# SEND MESSAGE
# ============================================
def send_message(prompt: str, model: str, language: str):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    
    payload = {
        "prompt": prompt,
        "model": model,
        "language": language
    }
    
    if st.session_state["conversation_id"]:
        payload["conversation_id"] = st.session_state["conversation_id"]
    
    try:
        response = requests.post(
            f"{API_URL}/ai/generate",
            json=payload,
            headers=get_headers(),
            timeout=300
        )
        
        if response.status_code == 200:
            data = response.json()
            st.session_state["conversation_id"] = data["conversation_id"]
            
            st.session_state["messages"].append({
                "role": "assistant",
                "code": data["code"],
                "explanation": data["explanation"],
                "review_notes": data["review_notes"]
            })
        else:
            error_msg = response.json().get("detail", "Unknown error")
            st.session_state["messages"].append({
                "role": "assistant",
                "content": f"❌ Error: {error_msg}"
            })
    except requests.exceptions.ReadTimeout:
        st.session_state["messages"].append({
            "role": "assistant",
            "content": "❌ Request timed out. Please try again."
        })
    except Exception as e:
        st.session_state["messages"].append({
            "role": "assistant",
            "content": f"❌ Error: {str(e)}"
        })

# ============================================
# MAIN APP LOGIC
# ============================================
if "token" not in st.session_state:
    show_login()
else:
    init_state()
    show_left_sidebar()
    
    # --- THREE COLUMN LAYOUT (Fixed, no scrolling) ---
    chat_col, spacer, settings_col = st.columns([5, 0.3, 1.5])
    
    # --- RIGHT SETTINGS PANEL ---
    with settings_col:
        st.markdown("## ⚙️ Settings")
        
        model = st.selectbox(
            "AI Model",
            options=["llama3.2:3b", "phi3:mini"],
            index=0,
            key="model_select"
        )
        
        language = st.selectbox(
            "Language",
            options=["python", "javascript", "typescript", "go", "rust", "sql", "bash"],
            index=0,
            key="lang_select"
        )
        
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1,
            help="0.0 = strict. 1.0 = creative.",
            key="temp_slider"
        )
        
        st.markdown("---")
        st.caption(f"Logged in as: **{st.session_state['username']}**")
        if st.button("🚪 Log Out", use_container_width=True, key="logout_btn"):
            do_logout()
    
    # --- MIDDLE COLUMN ---
    with chat_col:
        
        st.markdown("## 💻 AI Code Workspace")
        
        # SCROLLABLE CHAT WINDOW (Only this part scrolls!)
        chat_container = st.container(height=500)
        
        with chat_container:
            if not st.session_state["messages"]:
                st.markdown(
                    """
                    <div style="display: flex; justify-content: center; align-items: center; height: 420px; opacity: 0.3;">
                        <div style="text-align: center;">
                            <p style="font-size: 50px;">💬</p>
                            <p style="font-size: 22px; font-weight: 300;">Start a conversation</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                for msg in st.session_state["messages"]:
                    if msg["role"] == "user":
                        with st.chat_message("user"):
                            st.markdown(msg["content"])
                    else:
                        with st.chat_message("assistant"):
                            if "code" in msg:
                                st.code(msg["code"], language=language)
                                with st.expander("📝 Explanation"):
                                    st.markdown(msg.get("explanation", ""))
                                with st.expander("⚠️ Review Notes"):
                                    st.markdown(msg.get("review_notes", ""))
                            else:
                                st.markdown(msg.get("content", ""))
        
        # INPUT BOX (Below the chat, inside the column, not scrollable)
        with st.form("chat_form", clear_on_submit=True):
            input_col, btn_col = st.columns([6, 1])
            with input_col:
                user_input = st.text_input(
                    "Message",
                    placeholder="Describe what code you need...",
                    label_visibility="collapsed",
                    key="user_input"
                )
            with btn_col:
                submitted = st.form_submit_button("⬆️", use_container_width=True)
        
        if submitted and user_input:
            send_message(user_input, model, language)
            st.rerun()