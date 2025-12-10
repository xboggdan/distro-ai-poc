import streamlit as st
import openai
import google.generativeai as genai
import os
from google.api_core import exceptions

# --- PAGE SETUP ---
st.set_page_config(page_title="Fallback AI Chat")
st.title("Dual-Model Chat App")

# --- CONFIGURE APIS ---
openai_key = st.secrets.get("OPENAI_API_KEY")
gemini_key = st.secrets.get("GEMINI_API_KEY")
groq_key = st.secrets.get("GROQ_API_KEY")  # <--- NEW KEY FROM SECRETS

if gemini_key:
    genai.configure(api_key=gemini_key)

# --- HELPER FUNCTIONS ---

def get_openai_response(prompt):
    """Attempts to get a response from OpenAI (Paid)."""
    if not openai_key:
        raise ValueError("OpenAI API Key not found.")
    
    client = openai.OpenAI(api_key=openai_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", 
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Gemini Model Roster (Filtered to valid ones)
GEMINI_ROSTER = [
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro"
]

def get_backup_response(prompt):
    """
    FALLBACK LOGIC:
    1. Try Groq (Llama 3) - fast & free.
    2. If Groq fails, try Google Gemini loop.
    """
    
    # 1. TRY GROQ (Using OpenAI Client)
    if groq_key:
        try:
            # Groq is compatible with OpenAI's library!
            client = openai.OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=groq_key
            )
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Free, fast model
                messages=[{"role": "user", "content": prompt}]
            )
            return f"⚡ [Groq Llama3]: {response.choices[0].message.content}"
        except Exception as e:
            print(f"Groq failed: {e}")
    
    # 2. IF GROQ FAILS, TRY GEMINI
    if not gemini_key:
        return "❌ Error: No Groq or Gemini keys found."

    for model_name in GEMINI_ROSTER:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return f"✨ [Gemini {model_name}]: {response.text}"
            
        except exceptions.ResourceExhausted:
            print(f"⚠️ Quota hit for {model_name}. Switching...")
            continue
        except Exception as e:
            print(f"Error with {model_name}: {e}")
            continue

    return "❌ All systems down: OpenAI, Groq, and Gemini quotas exceeded."

# --- APP LOGIC ---

user_input = st.text_input("Ask me anything:")

if st.button("Submit") and user_input:
    response_text = ""
    used_model = ""
    
    # 1. TRY OPENAI FIRST
    try:
        with st.spinner("Trying OpenAI..."):
            response_text = get_openai_response(user_input)
            st.success("✅ Used Model: **OpenAI (GPT-3.5)**")
            st.write(response_text)
            
    except Exception as e_openai:
        print(f"OpenAI failed: {e_openai}")
        
        # 2. FALLBACK TO GROQ -> GEMINI
        try:
            with st.spinner("OpenAI failed. Trying backups (Groq/Gemini)..."):
                response_text = get_backup_response(user_input)
                
                if "Error" in response_text or "All systems down" in response_text:
                    st.error(response_text)
                else:
                    st.warning(f"⚠️ Backup Successful")
                    st.write(response_text)
                
        except Exception as e_backup:
            st.error("Critical Failure: All AI models failed.")
            st.error(f"Details: {e_backup}")

