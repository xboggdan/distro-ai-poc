import streamlit as st
import google.generativeai as genai
import os

st.title("🛠️ Gemini Model Diagnostic")

# 1. Get API Key
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("❌ Gemini API Key missing from secrets.")
else:
    # 2. Configure
    genai.configure(api_key=api_key)
    
    st.write(f"Testing API Key: `{api_key[:5]}...`")

    # 3. List Available Models
    try:
        st.subheader("Available Models for this Key:")
        models = list(genai.list_models())
        
        found_generating_models = []
        for m in models:
            # We only care about models that can 'generateContent'
            if 'generateContent' in m.supported_generation_methods:
                st.code(f"Model Name: {m.name}\nDisplay Name: {m.display_name}")
                found_generating_models.append(m.name)
        
        if not found_generating_models:
            st.warning("No text-generation models found. Check your Google AI Studio settings.")
        
    except Exception as e:
        st.error(f"Error listing models: {e}")
