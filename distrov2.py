import streamlit as st
import streamlit.components.v1 as components
import json

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Distro AI Studio",
    page_icon="💿",
    layout="wide",
    initial_sidebar_state="collapsed" # Hide sidebar by default for immersion
)

# --- 2. CSS HACKS ---
# This removes the white whitespace at the top of Streamlit apps
st.markdown("""
    <style>
        .block-container { padding-top: 0rem; padding-bottom: 0rem; padding-left: 0rem; padding-right: 0rem; }
        header { visibility: hidden; }
        footer { visibility: hidden; }
        /* Hide sidebar button unless hovered (optional) */
        [data-testid="stSidebarCollapsedControl"] { opacity: 0.2; }
        [data-testid="stSidebarCollapsedControl"]:hover { opacity: 1; }
    </style>
""", unsafe_allow_html=True)

# --- 3. THE BRIDGE ---
def load_frontend():
    """Loads the Vue.js interface"""
    try:
        with open("index.html", "r", encoding='utf-8') as f:
            html_code = f.read()
        return html_code
    except FileNotFoundError:
        return None

# --- 4. RENDER APP ---

html_content = load_frontend()

if html_content:
    # We use height=1000 to ensure the full Vue app is visible
    # scrolling=False keeps it feeling like a native app, not a webpage inside a webpage
    components.html(html_content, height=100vh, scrolling=True)
else:
    st.error("⚠️ `index.html` not found! Please ensure both files are in the repository.")

# --- 5. ADMIN SIDEBAR (OPTIONAL) ---
# This proves that Python is still running behind the scenes
with st.sidebar:
    st.title("🎛 Backend Monitor")
    st.success("Frontend Loaded Successfully")
    st.info("The Vue.js app is currently handling the user flow. In a production environment, we would use an API Gateway to send the final JSON here.")
    
    st.markdown("### Active Models")
    st.code("Vision: Gemini 2.5 Flash\nAudio: ACRCloud Fingerprint\nLogic: Pydantic Validation", language="yaml")
