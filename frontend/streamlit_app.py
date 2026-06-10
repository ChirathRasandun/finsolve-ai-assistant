import streamlit as st
import requests

# Page configuration
st.set_page_config(
    page_title="FinSolve AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# ---------------- CSS (CHAT BUBBLES) ----------------
st.markdown("""
<style>

.chat-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 10px;
}

/* Common bubble style */
.bubble {
    max-width: 70%;
    padding: 12px 16px;
    border-radius: 18px;
    font-size: 15px;
    line-height: 1.4;
    word-wrap: break-word;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

/* User bubble (RIGHT) */
.user-bubble {
    background: linear-gradient(135deg, #2196f3, #1976d2);
    color: white;
    align-self: flex-end;
    border-bottom-right-radius: 5px;
}

/* Bot bubble (LEFT) */
.bot-bubble {
    background: #f1f1f1;
    color: #000;
    align-self: flex-start;
    border-bottom-left-radius: 5px;
}

/* Wrapper to control alignment */
.message-row {
    display: flex;
    width: 100%;
}

/* Align right */
.right {
    justify-content: flex-end;
}

/* Align left */
.left {
    justify-content: flex-start;
}

/* Input styling */
.stChatInput input {
    font-size: 16px;
}

</style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "token" not in st.session_state:
    st.session_state.token = None

if "user" not in st.session_state:
    st.session_state.user = None

if "user_role" not in st.session_state:
    st.session_state.user_role = None

# ---------------- TITLE ----------------
st.title("🤖 FinSolve AI Assistant")
st.caption("Role-based intelligent company assistant")

# ---------------- SIDEBAR LOGIN ----------------
with st.sidebar:
    st.header("🔐 Authentication")

    if not st.session_state.token:
        with st.form("login_form"):
            username = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                try:
                    response = requests.post(
                        "http://localhost:8000/login",
                        params={"username": username, "password": password}
                    )

                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.token = data["access_token"]
                        st.session_state.user = data["user"]["username"]
                        st.session_state.user_role = data["user"]["role"]
                        st.success("Logged in")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
                except Exception as e:
                    st.error(f"Connection error: {e}")

    else:
        st.success("Logged in")
        st.markdown(f"**User:** {st.session_state.user}")
        st.markdown(f"**Role:** `{st.session_state.user_role}`")

        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

# ---------------- CHAT UI ----------------
st.divider()

chat_placeholder = st.container()

with chat_placeholder:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="message-row right">
                <div class="bubble user-bubble">
                     {msg["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)

        else:
            st.markdown(f"""
            <div class="message-row left">
                <div class="bubble bot-bubble">
                     {msg["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ---------------- INPUT ----------------
if st.session_state.token:
    prompt = st.chat_input("Ask me anything about the company...")

    if prompt:
        # save user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # call backend
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    "http://localhost:8000/query",
                    json={"query": prompt, "top_k": 5},
                    headers={"Authorization": f"Bearer {st.session_state.token}"}
                )

                if response.status_code == 200:
                    data = response.json()
                    answer = data["answer"]

                else:
                    answer = "Error getting response from server."

            except Exception as e:
                answer = f"Connection error: {e}"

        # save bot response
        st.session_state.messages.append({"role": "assistant", "content": answer})

        st.rerun()

else:
    st.info("Please login to start chatting")