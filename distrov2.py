import streamlit as st
import openai
import google.generativeai as genai
import os

# --- PAGE SETUP ---
st.set_page_config(page_title="Fallback AI Chat")
st.title("Dual-Model Chat App")

# --- CONFIGURE APIS ---
# Try to get keys from Streamlit Secrets
openai_key = st.secrets.get("OPENAI_API_KEY")
gemini_key = st.secrets.get("GEMINI_API_KEY")

# Configure Gemini if key exists
if gemini_key:
    genai.configure(api_key=gemini_key)

# --- HELPER FUNCTIONS ---

def get_openai_response(prompt):
    """Attempts to get a response from OpenAI."""
    if not openai_key:
        raise ValueError("OpenAI API Key not found.")
    
    client = openai.OpenAI(api_key=openai_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", # or gpt-4
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def get_gemini_response(prompt):
    """Attempts to get a response from Google Gemini."""
    if not gemini_key:
        raise ValueError("Gemini API Key not found.")
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text

# --- APP LOGIC ---

user_input = st.text_input("Ask me anything:")

if st.button("Submit") and user_input:
    response_text = ""
    used_model = ""
    
    # 1. TRY OPENAI FIRST
    try:
        with st.spinner("Trying OpenAI..."):
            response_text = get_openai_response(user_input)
            used_model = "OpenAI (GPT-3.5)"
            status_color = "green" # Success color
            
    except Exception as e_openai:
        # OpenAI failed, print error to console (optional) and try fallback
        print(f"OpenAI failed: {e_openai}")
        
        # 2. FALLBACK TO GEMINI
        try:
            with st.spinner("OpenAI failed. Switching to Google Gemini..."):
                response_text = get_gemini_response(user_input)
                used_model = "Google Gemini (Fallback)"
                status_color = "orange" # Warning color to indicate fallback
                
        except Exception as e_gemini:
            st.error(f"Both models failed. Please check your API keys/credits.\n\nError details: {e_gemini}")

    # --- DISPLAY RESULTS ---
    if response_text:
        # Show the User which model was used
        if "Fallback" in used_model:
            st.warning(f"⚠️ Used Model: **{used_model}**")
        else:
            st.success(f"✅ Used Model: **{used_model}**")
            
        st.write(response_text)
