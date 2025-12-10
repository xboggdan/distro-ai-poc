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
groq_key = st.secrets.get("GROQ_API_KEY")

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
    1. Try Groq (Llama 3.1) - fast & free.
    2. If Groq fails, try Google Gemini loop.
    """
    errors = [] # Keep track of what went wrong
    
    # 1. TRY GROQ (Using OpenAI Client)
    if groq_key:
        try:
            client = openai.OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=groq_key
            )
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",  # <--- UPDATED MODEL NAME
                messages=[{"role": "user", "content": prompt}]
            )
            return f"⚡ [Groq Llama 3.1]: {response.choices[0].message.content}"
        except Exception as e:
            # THIS IS THE CRITICAL CHANGE: We save the error to show you later
            error_msg = f"Groq Error: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
    else:
        errors.append("Groq Error: No API Key found in secrets.")
    
    # 2. IF GROQ FAILS, TRY GEMINI
    if not gemini_key:
        errors.append("Gemini Error: No API Key found.")
        return f"❌ Configuration Error: {errors}"

    for model_name in GEMINI_ROSTER:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return f"✨ [Gemini {model_name}]: {response.text}"
            
        except exceptions.ResourceExhausted:
            print(f"⚠️ Quota hit for {model_name}. Switching...")
            continue
        except Exception as e:
            errors.append(f"Gemini {model_name}: {str(e)}")
            continue

    # 3. IF EVERYTHING FAILS, SHOW THE LOGS
    return f"❌ ALL SYSTEMS FAILED.\n\n**Debug Logs:**\n" + "\n".join(errors)

# --- APP LOGIC ---

user_input = st.text_input("Ask me anything:")

if st.button("Submit") and user_input:
    response_text = ""
    
    # 1. TRY OPENAI FIRST
    try:
        with st.spinner("Trying OpenAI..."):
            response_text = get_openai_response(user_input)
            st.success("✅ Used Model: **OpenAI (GPT-3.5)**")
            st.write(response_text)
            
    except Exception as e_openai:
        # 2. FALLBACK TO GROQ -> GEMINI
        try:
            with st.spinner("OpenAI failed. Trying backups (Groq/Gemini)..."):
                response_text = get_backup_response(user_input)
                
                if "❌" in response_text:
                    st.error(response_text) # This will now show the REAL error
                else:
                    st.warning(f"⚠️ Backup Successful")
                    st.write(response_text)
                
        except Exception as e_backup:
            st.error("Critical Failure.")
            st.write(e_backup)
