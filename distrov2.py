import streamlit as st
import openai
import google.generativeai as genai
import os
from google.api_core import exceptions

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
    
    # Using the standard GPT-3.5 or 4 model
    client = openai.OpenAI(api_key=openai_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", 
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# List of models to try in order (Newest/Fastest -> Older/Slower)
MODEL_ROSTER = [
    "gemini-2.0-flash-exp",   # Try this first
    "gemini-1.5-flash",       # Standard fallback
    "gemini-1.5-flash-8b",    # Lightweight fallback
    "gemini-1.5-pro"          # Final resort
]

def get_gemini_response(prompt):
    """Attempts to get a response from Google Gemini with fallback."""
    
    # 1. Check if the key was actually loaded earlier
    # (Since you define gemini_key at line 13, we can check if it exists)
    if not st.secrets.get("GEMINI_API_KEY"):
        return "Error: GEMINI_API_KEY not found in secrets."

    # 2. Cycle through the models
    for model_name in MODEL_ROSTER:
        try:
            # Create the model instance
            model = genai.GenerativeModel(model_name)
            
            # Generate content
            response = model.generate_content(prompt)
            return response.text

        except exceptions.ResourceExhausted:
            # This is the 429 error. We catch it and loop to the next model.
            print(f"⚠️ Quota hit for {model_name}. Switching to next model...")
            continue
            
        except Exception as e:
            # Catch other random errors (like invalid model names)
            print(f"Error with {model_name}: {e}")
            continue

    # 3. If the loop finishes without returning, all models failed
    return "❌ Error: Daily quota exceeded for ALL free models. Please try again tomorrow."

def get_gemini_response(prompt):
    """Attempts to get a response from Google Gemini."""
    if not gemini_key:
        raise ValueError("Gemini API Key not found.")
    
    # UPDATED MODEL NAME HERE based on your diagnostic
    # We strip 'models/' and use just the name
    model = genai.GenerativeModel('gemini-2.5-flash') 
    response = model.generate_content(prompt)
    return response.text

# --- APP LOGIC ---

user_input = st.text_input("Ask me anything:")

if st.button("Submit") and user_input:
    response_text = ""
    used_model = ""
    status_color = ""
    
    # 1. TRY OPENAI FIRST
    try:
        with st.spinner("Trying OpenAI..."):
            response_text = get_openai_response(user_input)
            used_model = "OpenAI (GPT-3.5)"
            status_color = "green"
            
    except Exception as e_openai:
        print(f"OpenAI failed: {e_openai}")
        
        # 2. FALLBACK TO GEMINI
        try:
            with st.spinner("OpenAI failed. Switching to Google Gemini..."):
                response_text = get_gemini_response(user_input)
                used_model = "Google Gemini 2.5 Flash (Fallback)"
                status_color = "orange"
                
        except Exception as e_gemini:
            st.error("Both models failed.")
            st.error(f"OpenAI Error: {e_openai}")
            st.error(f"Gemini Error: {e_gemini}")

    # --- DISPLAY RESULTS ---
    if response_text:
        if "Fallback" in used_model:
            st.warning(f"⚠️ Used Model: **{used_model}**")
        else:
            st.success(f"✅ Used Model: **{used_model}**")
            
        st.write(response_text)


