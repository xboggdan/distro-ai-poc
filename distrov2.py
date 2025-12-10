import streamlit as st
import openai
import google.generativeai as genai
import os
from google.api_core import exceptions

# --- PAGE SETUP ---
st.set_page_config(page_title="Distro AI", layout="centered")
st.title("🤖 Distro AI Assistant")

# --- 1. THE BRAIN (PASTE YOUR RULES HERE) ---
# This is where you define your step orders and persona.
SYSTEM_RULES = """
You are a Music Distribution Expert named DistroBot.
Your goal is to guide the user through releasing a track.

RULES:
1. Do NOT give long generic lists.
2. Follow these steps strictly in order:
   - Step 1: Ask for the Artist Name.
   - Step 2: Ask for the Track Title.
   - Step 3: Ask for the Genre.
   - Step 4: Confirm all details.
3. Wait for the user to answer before moving to the next step.
4. Keep answers short and professional.
"""

# --- CONFIGURE APIS ---
openai_key = st.secrets.get("OPENAI_API_KEY")
gemini_key = st.secrets.get("GEMINI_API_KEY")
groq_key = st.secrets.get("GROQ_API_KEY")

if gemini_key:
    genai.configure(api_key=gemini_key)

# --- SESSION STATE (MEMORY) ---
# This remembers the chat history so the bot knows "Step 1" is done.
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- HELPER FUNCTIONS ---

def get_smart_response(user_prompt, chat_history):
    """
    Decides which AI to use (OpenAI -> Groq -> Gemini) 
    and sends the FULL history + Rules.
    """
    
    # PREPARE MESSAGES FOR OPENAI/GROQ
    # Structure: [System Rules] + [Previous Chat] + [New User Message]
    messages_payload = [{"role": "system", "content": SYSTEM_RULES}]
    
    # Add history from session state
    for msg in chat_history:
        messages_payload.append({"role": msg["role"], "content": msg["content"]})
    
    # Add the latest user prompt
    messages_payload.append({"role": "user", "content": user_prompt})

    # 1. TRY OPENAI (If key exists)
    if openai_key:
        try:
            client = openai.OpenAI(api_key=openai_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo", 
                messages=messages_payload
            )
            return response.choices[0].message.content, "OpenAI"
        except Exception:
            pass # Fail silently to backup

    # 2. TRY GROQ (The Best Free Backup)
    if groq_key:
        try:
            client = openai.OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=groq_key
            )
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant", 
                messages=messages_payload
            )
            return response.choices[0].message.content, "Groq (Llama 3.1)"
        except Exception as e:
            print(f"Groq Error: {e}")

    # 3. TRY GEMINI (Last Resort)
    # Gemini behaves differently, so we convert history to a string script.
    if gemini_key:
        try:
            # Convert list of messages to a single string for Gemini
            full_transcript = f"{SYSTEM_RULES}\n\n"
            for msg in messages_payload:
                if msg['role'] != 'system':
                    full_transcript += f"{msg['role'].upper()}: {msg['content']}\n"
            
            # Using the safest model
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(full_transcript)
            return response.text, "Gemini"
        except Exception as e:
            return f"❌ Error: {e}", "Error"

    return "❌ No API keys found. Please check secrets.", "Error"

# --- CHAT INTERFACE ---

# 1. Display previous chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 2. Chat Input Box
if prompt := st.chat_input("Type your answer here..."):
    # Show user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add to specific history logic (We don't add to session_state yet, 
    # we pass the *existing* state + new prompt to the AI)
    
    with st.spinner("Thinking..."):
        # Call the AI function
        response_text, provider = get_smart_response(prompt, st.session_state.messages)
        
        # Display Bot Response
        with st.chat_message("assistant"):
            if provider != "OpenAI":
                st.caption(f"⚡ using {provider}") # Show which free model helped
            st.markdown(response_text)
    
    # 3. Save to History (So it remembers for next time)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": response_text})

# Button to clear memory if testing
if st.sidebar.button("Reset Conversation"):
    st.session_state.messages = []
    st.rerun()
