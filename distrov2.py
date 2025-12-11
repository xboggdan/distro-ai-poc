import streamlit as st
import time
import re

# --- 1. CONFIGURATION & PROFESSIONAL STYLING ---
st.set_page_config(page_title="DistroBot Pro", page_icon="💿", layout="wide")

st.markdown("""
<style>
    /* --- GLOBAL THEME: Clean, Professional, 'Spotify for Artists' Vibe --- */
    
    /* Main Background & Text */
    .stApp {
        background-color: #FAFAFA; /* Soft White */
        color: #1a1a1a;
    }

    /* Chat Bubbles */
    .stChatMessage {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        padding: 15px;
        margin-bottom: 12px;
    }
    
    /* User Message Difference */
    div[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #F4F7F9; /* Very subtle blue-grey for user */
    }

    /* INPUT FIELD: Floating & Clean */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 1px solid #ddd;
        padding: 10px;
    }

    /* SIDEBAR: The "Live Preview" Pane */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #EAEAEA;
    }

    /* --- CUSTOM UI COMPONENTS --- */

    /* 1. The Live Release Card (HTML/CSS) */
    .preview-card {
        border: 1px solid #eee;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        background: white;
        margin-bottom: 20px;
    }
    .preview-img {
        width: 100%;
        height: 250px;
        background-color: #f0f0f0;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #aaa;
        font-size: 0.9em;
        background-size: cover;
        background-position: center;
    }
    .preview-content { padding: 15px; }
    .preview-title { font-weight: 700; font-size: 1.1em; color: #111; margin-bottom: 4px; }
    .preview-artist { font-size: 0.9em; color: #555; }
    .preview-badge { 
        display: inline-block; font-size: 0.7em; padding: 2px 8px; 
        border-radius: 10px; background: #eee; color: #666; margin-top: 10px; 
    }

    /* 2. Tech Badges (The "Brain" Indicators) */
    .logic-badge {
        font-family: 'SF Mono', 'Courier New', monospace;
        font-size: 0.7em;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 6px;
        background-color: #e3f2fd; 
        color: #1565c0;
        border: 1px solid #bbdefb;
        display: inline-block;
        margin-top: 8px;
    }
    .badge-alert { background-color: #ffebee; color: #c62828; border-color: #ffcdd2; }
    .badge-success { background-color: #e8f5e9; color: #2e7d32; border-color: #c8e6c9; }

</style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE & DATA STRUCTURE ---

def init_state():
    # Define the defaults for a robust session
    defaults = {
        "history": [
            {
                "role": "assistant", 
                "content": "👋 **Hello.** I am your Distribution Agent.\n\nI ensure your metadata meets DSP (Spotify/Apple) standards to prevent rejection.\n\nLet's start. What is the **Release Title**?",
                "badge": "System Ready",
                "type": "info"
            }
        ],
        "step": "TITLE", # TITLE, ARTIST, COVER, COVER_FIX, AUDIO, REVIEW
        "payload": {
            "title": "",
            "artist": "",
            "version": "Original",
            "is_cover": False,
            "explicit": False
        },
        "temp_cover": None,
        "flags": [] # To store warnings
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# --- 3. THE LOGIC BRAIN (Complex Rules Engine) ---

def add_msg(role, text, badge=None, badge_type="normal"):
    """Helper to append messages to history"""
    st.session_state.history.append({
        "role": role, 
        "content": text, 
        "badge": badge,
        "type": badge_type
    })

def process_logic(user_input, input_type="text"):
    """
    The Core 'Agent' Function. 
    It mimics a backend API processing requests and updating state.
    """
    step = st.session_state.step
    payload = st.session_state.payload
    
    # --- LOGIC: TITLE HANDLING ---
    if step == "TITLE":
        # 1. Capture User Input
        add_msg("user", user_input)
        
        # 2. Run Guardrails (The "Basic Logic" Fix)
        # Check for "Feat." in title (DSP Violation)
        if re.search(r"(?i)\bfeat\.?|\bft\.?", user_input):
            clean_title = re.sub(r"(?i)\s*\(?(feat\.?|ft\.?).*?\)?", "", user_input).strip()
            payload['title'] = clean_title
            
            warn_msg = f"I detected feature artist info in the title ('{user_input}').\n\n**Protocol:** Feature artists must be listed in a separate field, not the title. I have cleaned it to: **{clean_title}**."
            add_msg("assistant", warn_msg, "Metadata Guardrail | Regex Cleaner", "alert")
        else:
            payload['title'] = user_input
            add_msg("assistant", f"Title set: **{payload['title']}**.", "Logic Engine", "success")

        # 3. Move Next
        add_msg("assistant", "Who is the **Primary Artist**?", "Flow Control")
        st.session_state.step = "ARTIST"

    # --- LOGIC: ARTIST HANDLING ---
    elif step == "ARTIST":
        add_msg("user", user_input)
        payload['artist'] = user_input
        
        add_msg("assistant", "Artist logged. Now, please upload the **Cover Art**.", "Asset Manager")
        st.session_state.step = "COVER"

    # --- LOGIC: COVER ART ANALYSIS (Vision AI) ---
    elif step == "COVER":
        # Input is file
        add_msg("user", "📁 Image Uploaded")
        st.session_state.temp_cover = user_input # In real app, save S3 URL
        
        # Simulate Vision API
        with st.spinner("🧠 Vision Model analyzing for Text & Guidelines..."):
            time.sleep(1.5)
        
        # Hardcoded logic for demo: We pretend we found text
        found_issue = True 
        
        if found_issue:
            msg = "⚠️ **Issue Detected:** The Vision model found text: *'Listen Now on Spotify'*.\n\nDSPs reject artwork with marketing text. I can use Generative Fill to remove it."
            add_msg("assistant", msg, "Google Gemini Vision | OCR", "alert")
            st.session_state.step = "COVER_FIX"
        else:
            st.session_state.step = "AUDIO"

    # --- LOGIC: COVER FIX (Gen AI) ---
    elif step == "COVER_FIX":
        if user_input == "FIX":
            add_msg("user", "✨ Fix it automatically")
            with st.spinner("🎨 Generative In-painting..."):
                time.sleep(2)
            add_msg("assistant", "Cleaned artwork generated. Proceeding to Audio.", "Stable Diffusion | In-painting", "success")
        else:
            add_msg("user", "Keep original (I will risk rejection)")
            add_msg("assistant", "Noted. Flagged as 'High Risk'.")
            
        st.session_state.step = "AUDIO"
        add_msg("assistant", "Please upload the **Master Audio** (WAV).", "Asset Manager")

    # --- LOGIC: AUDIO FINGERPRINTING ---
    elif step == "AUDIO":
        add_msg("user", "🎵 Audio Uploaded")
        
        with st.spinner("🎧 ACR Cloud Fingerprinting..."):
            time.sleep(2)
            
        # Mock Copyright Match
        msg = "⚠️ **Copyright Match:** Audio matches *'Shape of You' (Ed Sheeran)*.\n\nIs this a **Cover Song** or an **Original**?"
        add_msg("assistant", msg, "ACR Cloud | Content ID", "alert")
        st.session_state.step = "RIGHTS"

    # --- LOGIC: RIGHTS & FINISH ---
    elif step == "RIGHTS":
        if user_input == "Cover":
            payload['is_cover'] = True
            add_msg("user", "It's a Cover")
            add_msg("assistant", "Marked as Cover. We will secure the Mechanical License via Harry Fox Agency.", "Legal Logic", "success")
        else:
            payload['is_cover'] = False
            add_msg("user", "It's Original")
            add_msg("assistant", "Marked as Original.", "Legal Logic")
            
        st.session_state.step = "DONE"
        add_msg("assistant", "🎉 **Release Ready.** Review the final data in the sidebar.", "System", "success")


# --- 4. UI: SIDEBAR PREVIEW (The "Live Connection") ---

with st.sidebar:
    st.title("🎛 Control Center")
    st.markdown("---")
    
    # LIVE PREVIEW CARD
    p = st.session_state.payload
    
    # Determine Image URL
    if st.session_state.temp_cover:
        # Just a placeholder for the demo since we can't easily display raw bytes object in HTML string without processing
        img_url = "https://images.unsplash.com/photo-1619983081563-430f63602796?q=80&w=1000&auto=format&fit=crop"
    else:
        img_url = "" # CSS handles empty state
        
    # Render HTML Card
    card_html = f"""
    <div class="preview-card">
        <div class="preview-img" style="background-image: url('{img_url}');">
            {'' if img_url else 'Pending Art'}
        </div>
        <div class="preview-content">
            <div class="preview-title">{p['title'] or "Untitled Release"}</div>
            <div class="preview-artist">{p['artist'] or "Unknown Artist"}</div>
            <span class="preview-badge">{'Cover Song' if p['is_cover'] else 'Original'}</span>
        </div>
    </div>
    """
    st.markdown("### 👁‍🗨 Live Preview")
    st.markdown(card_html, unsafe_allow_html=True)
    
    # RAW DATA VIEW
    with st.expander("🛠 Raw JSON Payload"):
        st.json(st.session_state.payload)
        
    st.markdown("---")
    if st.button("Reset Session"):
        st.session_state.clear()
        st.rerun()

# --- 5. UI: MAIN CHAT INTERFACE ---

st.title("Distribution Agent")

# Render History
for msg in st.session_state.history:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])
        
        # Render Badge if exists
        if msg.get('badge'):
            b_type = "badge-alert" if msg['type'] == 'alert' else "badge-success" if msg['type'] == 'success' else ""
            st.markdown(f"<div class='logic-badge {b_type}'>⚙️ {msg['badge']}</div>", unsafe_allow_html=True)

# --- 6. DYNAMIC INPUT ZONES ---

st.markdown("---")
current_step = st.session_state.step

# A. TEXT INPUTS
if current_step in ["TITLE", "ARTIST"]:
    val = st.chat_input(f"Enter {current_step.title()}...")
    if val:
        process_logic(val)

# B. FILE UPLOADS
elif current_step == "COVER":
    with st.chat_message("assistant"):
        st.write("waiting for file...")
        f = st.file_uploader("Upload 3000x3000px JPG", type=['jpg','png'], label_visibility="collapsed")
        if f: process_logic(f, "file")

elif current_step == "AUDIO":
    with st.chat_message("assistant"):
        st.write("waiting for file...")
        f = st.file_uploader("Upload WAV/MP3", type=['wav','mp3'], label_visibility="collapsed")
        if f: process_logic(f, "file")

# C. BUTTON DECISIONS
elif current_step == "COVER_FIX":
    col1, col2 = st.columns(2)
    if col1.button("✨ Auto-Fix (Gen AI)", use_container_width=True):
        process_logic("FIX", "btn")
    if col2.button("Keep As Is", use_container_width=True):
        process_logic("SKIP", "btn")

elif current_step == "RIGHTS":
    col1, col2 = st.columns(2)
    if col1.button("This is a Cover", use_container_width=True):
        process_logic("Cover", "btn")
    if col2.button("This is Original", use_container_width=True):
        process_logic("Original", "btn")

elif current_step == "DONE":
    st.balloons()
