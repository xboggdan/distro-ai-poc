import streamlit as st
import streamlit.components.v1 as components

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Distro AI Studio",
    page_icon="💿",
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# --- 2. CSS HACKS ---
# This removes the white whitespace at the top of Streamlit apps
st.markdown("""
    <style>
        .block-container { padding-top: 0rem; padding-bottom: 0rem; padding-left: 0rem; padding-right: 0rem; }
        header { visibility: hidden; }
        footer { visibility: hidden; }
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
    # FIXED LINE BELOW: Changed '100vh' to 1200 (pixels)
    components.html(html_content, height=1200, scrolling=True)
else:
    st.error("⚠️ `index.html` not found! Please ensure both files are in the repository.")

# --- 5. ADMIN SIDEBAR ---
with st.sidebar:
    st.title("🎛 Backend Monitor")
    st.success("Frontend Loaded Successfully")
    st.info("The Vue.js app is currently handling the user flow.")
    
    st.markdown("### Active Models")
    st.code("Vision: Gemini 2.5 Flash\nAudio: ACRCloud Fingerprint\nLogic: Pydantic Validation", language="yaml")
