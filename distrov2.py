import streamlit as st
import time

# --- 1. IMPORT & SETUP ---
st.set_page_config(page_title="DistroBot AI Debugger", page_icon="🔧", layout="wide")

# Debug Flag: Check if libraries are installed
libs_status = {}
try:
    from groq import Groq
    libs_status["groq"] = "✅ Installed"
except ImportError as e:
    libs_status["groq"] = f"❌ Missing ({e})"

try:
    import google.generativeai as genai
    libs_status["gemini"] = "✅ Installed"
except ImportError as e:
    libs_status["gemini"] = f"❌ Missing ({e})"

try:
    from openai import OpenAI
    libs_status["openai"] = "✅ Installed"
except ImportError as e:
    libs_status["openai"] = f"❌ Missing ({e})"

# --- 2. THE TEST LOGIC ---

def test_groq():
    if "GROQ_API_KEY" not in st.secrets:
        return "⚠️ Key missing in secrets"
    
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        # Simple test call
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": "Say hello"}],
            model="llama3-8b-8192",
        )
        return f"✅ Success! Response: {completion.choices[0].message.content}"
    except Exception as e:
        return f"❌ Failed: {str(e)}"

def test_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        return "⚠️ Key missing in secrets"
        
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Say hello")
        return f"✅ Success! Response: {response.text}"
    except Exception as e:
        return f"❌ Failed: {str(e)}"

# --- 3. THE UI ---

st.title("🔧 AI Connection Doctor")

st.markdown("### 1. Library Status")
c1, c2, c3 = st.columns(3)
c1.info(f"Groq Lib: {libs_status['groq']}")
c2.info(f"Gemini Lib: {libs_status['gemini']}")
c3.info(f"OpenAI Lib: {libs_status['openai']}")

st.markdown("### 2. Secret Keys Detected")
found_secrets = list(st.secrets.keys())
# Hide actual values for security, just show we found the key
safe_view = {k: "******" for k in found_secrets}
st.json(safe_view)

st.markdown("### 3. Connection Test")
if st.button("🚀 Run Connection Test"):
    
    with st.spinner("Testing Groq..."):
        g_res = test_groq()
    
    with st.spinner("Testing Gemini..."):
        gem_res = test_gemini()
        
    st.subheader("Results:")
    
    # GROQ RESULT
    if "Success" in g_res:
        st.success(f"**Groq:** {g_res}")
    else:
        st.error(f"**Groq:** {g_res}")
        
    # GEMINI RESULT
    if "Success" in gem_res:
        st.success(f"**Gemini:** {gem_res}")
    else:
        st.error(f"**Gemini:** {gem_res}")

st.divider()
st.info("If you see '401 Unauthorized' or 'Invalid Key', regenerate your API key in the provider's console.")
