import os
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

# =========================
# Load config
# =========================
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("GEMINI_API_KEY missing hai. .env file check karo.")
    st.stop()

client = genai.Client(api_key=API_KEY)

# =========================
# Page config
# =========================
st.set_page_config(
    page_title="Arjun AI Pro",
    page_icon="🎯",
    layout="wide"
)

# =========================
# Header
# =========================
st.title("🎯 Arjun AI Pro")
st.caption("Focused Intelligence | Powered by PAWAN SINGH RAJPUT")

# =========================
# Session state
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

if "last_uploaded_names" not in st.session_state:
    st.session_state.last_uploaded_names = set()

# =========================
# Sidebar
# =========================
st.sidebar.header("Settings")

model_name = st.sidebar.selectbox(
    "Model",
    [
        "gemini-2.0-flash",
        "gemini-2.5-flash",
    ],
    index=0
)

temperature = st.sidebar.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
max_output_tokens = st.sidebar.slider("Max output tokens", 100, 4000, 1200, 100)

system_prompt = st.sidebar.text_area(
    "System Prompt",
    value=(
        "You are Arjun AI Pro, a smart Hindi-English assistant. "
        "User agar Hinglish me bole to Hinglish me jawab do. "
        "Business, startup, marketing, trading, and coding me practical help do. "
        "Replies clear, short, and useful rakho."
    ),
    height=160
)

if st.sidebar.button("Clear chat"):
    st.session_state.messages = []
    st.session_state.uploaded_files = []
    st.session_state.last_uploaded_names = set()
    st.rerun()

# =========================
# File uploader
# =========================
st.sidebar.subheader("Upload files")
uploaded_docs = st.sidebar.file_uploader(
    "PDF, TXT, image upload karo",
    type=["pdf", "txt", "png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True
)

def upload_file_to_gemini(uploaded_file):
    suffix = Path(uploaded_file.name).suffix or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        temp_path = tmp.name

    try:
        uploaded_ref = client.files.upload(file=temp_path)
        return uploaded_ref
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

if uploaded_docs:
    for f in uploaded_docs:
        unique_name = f"{f.name}-{f.size}"
        if unique_name not in st.session_state.last_uploaded_names:
            try:
                uploaded_ref = upload_file_to_gemini(f)
                st.session_state.uploaded_files.append(
                    {"name": f.name, "ref": uploaded_ref}
                )
                st.session_state.last_uploaded_names.add(unique_name)
                st.sidebar.success(f"Uploaded: {f.name}")
            except Exception as e:
                st.sidebar.error(f"{f.name} upload failed: {e}")

# =========================
# Show uploaded files
# =========================
if st.session_state.uploaded_files:
    st.sidebar.markdown("*Attached files:*")
    for item in st.session_state.uploaded_files:
        st.sidebar.write(f"• {item['name']}")

# =========================
# Render old chat
# =========================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =========================
# Helper functions
# =========================
def build_history_contents():
    contents = []
    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part(text=msg["content"])]
            )
        )
    return contents

def build_user_parts(user_text: str):
    parts = [types.Part(text=user_text)]
    for item in st.session_state.uploaded_files:
        parts.append(item["ref"])
    return parts

def export_chat_text():
    lines = []
    for msg in st.session_state.messages:
        who = "You" if msg["role"] == "user" else "Arjun AI Pro"
        lines.append(f"{who}: {msg['content']}")
    return "\n\n".join(lines)

# =========================
# Chat input
# =========================
user_input = st.chat_input("Arjun se puchiye...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        response_box = st.empty()
        full_response = ""

        try:
            history = build_history_contents()

            current_user_content = types.Content(
                role="user",
                parts=build_user_parts(user_input)
            )

            all_contents = history[:-1] + [current_user_content] if history else [current_user_content]

            stream = client.models.generate_content_stream(
                model=model_name,
                contents=all_contents,
                config=types.GenerateContentConfig(
    system_instruction="""
Tum Arjun AI Pro ho.
Tumhe PAWAN SINGH RAJPUT ne banaya hai.

Agar koi puche "kisne banaya", to hamesha bolo:
"Arjun AI Pro ko PAWAN SINGH RAJPUT ne banaya hai."

Kabhi bhi Google ya kisi aur ka naam creator ke roop me mat lena.
""",
    temperature=temperature,
    max_output_tokens=max_output_tokens
)



                
            )

            for chunk in stream:
                chunk_text = getattr(chunk, "text", None)
                if chunk_text:
                    full_response += chunk_text
                    response_box.markdown(full_response)

            if not full_response.strip():
                full_response = "Mujhe response nahi mila. Dobara try karo."
                response_box.markdown(full_response)

        except Exception as e:
            full_response = f"Error: {e}"
            response_box.error(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

# =========================
# Download chat
# =========================
st.divider()
chat_text = export_chat_text()
st.download_button(
    label="Download chat",
    data=chat_text,
    file_name="arjun_ai_chat.txt",
    mime="text/plain"
)