from typing import Set
from Backend.core import run_llm
import streamlit as st
import uuid
from datetime import datetime

st.set_page_config(page_title="Documentation Helper Bot", layout="wide")

# Initialize session state
if "chat_sessions" not in st.session_state:
    st.session_state["chat_sessions"] = {}
if "current_session_id" not in st.session_state:
    # Create initial session
    session_id = str(uuid.uuid4())
    st.session_state["current_session_id"] = session_id
    st.session_state["chat_sessions"][session_id] = {
        "name": f"Chat {datetime.now().strftime('%m/%d %H:%M')}",
        "chat_answer_history": [],
        "user_prompt_history": [],
        "chat_history": [],
        "created_at": datetime.now()
    }

# Sidebar for chat history
with st.sidebar:
    st.header("Chat History")
    
    # New Chat button
    if st.button("➕ New Chat", use_container_width=True):
        session_id = str(uuid.uuid4())
        st.session_state["current_session_id"] = session_id
        st.session_state["chat_sessions"][session_id] = {
            "name": f"Chat {datetime.now().strftime('%m/%d %H:%M')}",
            "chat_answer_history": [],
            "user_prompt_history": [],
            "chat_history": [],
            "created_at": datetime.now()
        }
        st.rerun()
    
    st.divider()
    
    # List previous chats (sorted by creation time, most recent first)
    sorted_sessions = sorted(
        st.session_state["chat_sessions"].items(),
        key=lambda x: x[1]["created_at"],
        reverse=True
    )
    
    for session_id, session_data in sorted_sessions:
        # Show current session differently
        if session_id == st.session_state["current_session_id"]:
            st.markdown(f"**🟢 {session_data['name']}**")
        else:
            if st.button(f"💬 {session_data['name']}", key=session_id, use_container_width=True):
                st.session_state["current_session_id"] = session_id
                st.rerun()
        
        # Show message count
        msg_count = len(session_data["user_prompt_history"])
        if msg_count > 0:
            st.caption(f"{msg_count} message{'s' if msg_count != 1 else ''}")
    
    # Clear all chats button
    st.divider()
    if st.button("🗑️ Clear All Chats", type="secondary", use_container_width=True):
        # Keep current session but clear others
        current_session = st.session_state["chat_sessions"][st.session_state["current_session_id"]]
        st.session_state["chat_sessions"] = {st.session_state["current_session_id"]: current_session}
        st.rerun()

# Main chat interface
st.header("Documentation Helper Bot")

# Get current session data
current_session = st.session_state["chat_sessions"][st.session_state["current_session_id"]]

# Chat input form
with st.form("chat_form", clear_on_submit=True):
    prompt = st.text_input("Ask your question about Langchain:", placeholder="Enter your question here...")
    submit_button = st.form_submit_button("Send Message", use_container_width=True, type="primary")

def create_sources_string(source_urls: Set[str]) -> str:
    if not source_urls:
        return ""
    sources_list = sorted(list(source_urls))
    sources_string = "sources:\n"
    for i, source in enumerate(sources_list):
        sources_string += f"{i+1}. {source}\n"
    return sources_string

# Process the submitted form
if submit_button and prompt:
    with st.spinner("Generating response..."):
        generated_response = run_llm(query=prompt, chat_history=current_session["chat_history"])
        sources = set(doc.metadata["source"] for doc in generated_response["source_documents"])

        formatted_response = (
            f"{generated_response['result']}\n\n{create_sources_string(sources)}"
        )    

        current_session["user_prompt_history"].append(prompt)
        current_session["chat_answer_history"].append(formatted_response)
        current_session["chat_history"].append(("human", prompt))
        current_session["chat_history"].append(("ai", generated_response["result"]))
        
        # Update session name with first question if this is the first message
        if len(current_session["user_prompt_history"]) == 1:
            # Use first few words of the question as session name
            session_name = prompt[:30] + "..." if len(prompt) > 30 else prompt
            current_session["name"] = session_name
        
        st.rerun()

# Display chat history (bottom-to-top flow)
st.subheader("Conversation")

# Create a container for the chat messages
chat_container = st.container()

with chat_container:
    if current_session["chat_answer_history"]:
        # Display messages in chronological order (oldest first, newest at bottom)
        for user_query, generated_response in zip(current_session["user_prompt_history"], current_session["chat_answer_history"]):
            # User message
            with st.chat_message("user"):
                st.write(user_query)
            
            # Assistant message
            with st.chat_message("assistant"):
                st.write(generated_response)
    else:
        st.info("👋 Welcome! Ask me anything about Langchain documentation.")

# Auto-scroll to bottom (this will show the latest messages)
if current_session["chat_answer_history"]:
    # Add some space at the bottom
    st.write("")
