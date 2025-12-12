import streamlit as st
import time
import re

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="DistroBot Pro", page_icon="💿", layout="wide")

st.markdown("""
<style>
    /* Global Clean Theme */
    .stApp { background-color: #FAFAFA; color: #1a1a1a; }
    
    /* Chat Bubbles */
    .stChatMessage {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        padding: 15px;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input { border-radius: 10px; }
    
    /* Sidebar Preview Card */
    .preview-card {
        border: 1px solid #eee;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        background: white;
        margin-bottom: 20px;
    }
    .preview-img {
        width: 100%; height: 250px; background-color: #f0f0f0;
        display: flex; align-items: center; justify-content: center;
        color: #aaa; background-size: cover; background-position: center;
    }
    .preview-content { padding: 15px; }
    .preview-title { font-weight: 700; font-size: 1.1em; color: #111; margin-bottom: 4px; }
    .preview-artist { font-size: 0.9em; color: #555; }
    
    /* Tech Badges */
    .logic-badge {
        font-size: 0.7em; padding: 4px 8px; border-radius: 6px;
        background-color: #e3f2fd; color: #1565c0; border: 1px solid #bbdefb;
        display: inline-block; margin-top: 8px; font-weight: 600;
    }
    .badge-alert { background-color: #ffebee; color: #c62828; border-color: #ffcdd2; }
</style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE ---

def init_state():
    defaults = {
        "history": [{
            "role": "assistant", 
            "content": "👋 **Hello.** I am your Distribution Agent.\n\nI ensure your metadata meets DSP standards. Let's start.\n\nWhat is the **Release Title**?",
            "badge": "System Ready", "type": "info"
        }],
        "step": "TITLE",
        "payload": {
            "title": "", "artist": "", "version": "Original", "is_cover": False
        },
        "temp_cover": None,
        "processing": False # UI blocker state
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# --- 3. LOGIC HANDLERS (CALLBACKS) ---
# These run BEFORE the page reloads, fixing the "Double Click" bug.

def add_msg(role, text, badge=None, b_type="normal"):
    st.session_state.history.append({
        "role": role, "content": text, "badge": badge, "type": b_type
    })

def handle_text_input():
    """Callback for chat_input"""
    # Get the value from the widget key
    user_val = st.session_state.user_input_widget
    if not user_val: return
    
    step = st.session_state.step
    
    # --- STEP 1: TITLE ---
    if step == "TITLE":
        add_msg("user", user_val)
        
        # Guardrail Logic
        if re.search(r"(?i)\bfeat\.?|\bft\.?", user_val):
            clean = re.sub(r"(?i)\s*\(?(feat\.?|ft\.?).*?\)?", "", user_val).strip()
            st.session_state.payload['title'] = clean
            add_msg("assistant", f"I removed 'feat' from the title to comply with Style Guide.\nTitle set to: **{clean}**", "Metadata Guardrail", "alert")
        else:
            st.session_state.payload['title'] = user_val
            add_msg("assistant", f"Title set: **{user_val}**", "Logic Engine", "success")
            
        add_msg("assistant", "Who is the **Primary Artist**?", "Flow Control")
        st.session_state.step = "ARTIST"

    # --- STEP 2: ARTIST ---
    elif step == "ARTIST":
        add_msg("user", user_val)
        st.session_state.payload['artist'] = user_val
        add_msg("assistant", "Artist set. Please upload **Cover Art**.", "Asset Manager")
        st.session_state.step = "COVER"

def handle_file_upload():
    """Callback for file uploader"""
    f = st.session_state.uploaded_file
    if f is None: return

    step = st.session_state.step
    
    if step == "COVER":
        add_msg("user", "📁 Image Uploaded")
        st.session_state.temp_cover = True # Flag to show image in preview
        
        # Mock Processing
        with st.spinner("Analyzing Image..."):
            time.sleep(1) # Simulated delay
            
        # Hardcoded Logic: Assume issue found for demo
        add_msg("assistant", "⚠️ **Vision Issue:** Text detected ('Listen Now').\nDSPs reject marketing text on covers.", "Gemini Vision | OCR", "alert")
        st.session_state.step = "COVER_FIX"

    elif step == "AUDIO":
        add_msg("user", "🎵 Audio Uploaded")
        with st.spinner("Fingerprinting Audio..."):
            time.sleep(1)
            
        add_msg("assistant", "⚠️ **Copyright Match:** 'Shape of You'.\nIs this a Cover or Original?", "ACR Cloud", "alert")
        st.session_state.step = "RIGHTS"

def handle_button_click(choice):
    """Callback for buttons"""
    step = st.session_state.step
    
    if step == "COVER_FIX":
        if choice == "FIX":
            add_msg("user", "✨ Fix it automatically")
            add_msg("assistant", "Artwork cleaned. Proceeding to Audio.", "Gen AI", "success")
        else:
            add_msg("user", "Keep Original")
            add_msg("assistant", "Keeping original (High Risk). Upload Audio.", "Logic")
        st.session_state.step = "AUDIO"

    elif step == "RIGHTS":
        if choice == "COVER":
            st.session_state.payload['is_cover'] = True
            add_msg("user", "It's a Cover")
            add_msg("assistant", "Marked as Cover. Licensing initiated.", "Legal Logic")
        else:
            st.session_state.payload['is_cover'] = False
            add_msg("user", "It's Original")
            add_msg("assistant", "Marked as Original.", "Legal Logic")
        
        st.session_state.step = "DONE"
        add_msg("assistant", "🎉 **Ready!** Review sidebar.", "System")


# --- 4. SIDEBAR PREVIEW ---
with st.sidebar:
    st.title("🎛 Control Center")
    st.markdown("---")
    
    p = st.session_state.payload
    
    # Dynamic Image URL
    img_bg = ""
    img_text = "Pending Art"
    if st.session_state.temp_cover:
        img_bg = "background-image: url('https://images.unsplash.com/photo-1619983081563-430f63602796?q=80&w=1000&auto=format&fit=crop');"
        img_text = ""

    st.markdown(f"""
    <div class="preview-card">
        <div class="preview-img" style="{img_bg}">
            {img_text}
        </div>
        <div class="preview-content">
            <div class="preview-title">{p['title'] or "Untitled Release"}</div>
            <div class="preview-artist">{p['artist'] or "Unknown Artist"}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("JSON Payload"):
        st.json(p)
    
    if st.button("Reset"):
        st.session_state.clear()
        st.rerun()

# --- 5. MAIN CHAT RENDER ---
st.title("Distribution Agent")

# Display History
for msg in st.session_state.history:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])
        if msg.get('badge'):
            c = "badge-alert" if msg['type'] == "alert" else "logic-badge"
            st.markdown(f"<div class='{c}'>⚙️ {msg['badge']}</div>", unsafe_allow_html=True)

# --- 6. INPUT AREA (CONTEXT AWARE) ---
st.markdown("---")
step = st.session_state.step

# 1. TEXT INPUT (With on_submit callback)
if step in ["TITLE", "ARTIST"]:
    st.chat_input(
        placeholder="Type here...",
        key="user_input_widget",
        on_submit=handle_text_input
    )

# 2. FILE UPLOAD (With on_change callback)
elif step in ["COVER", "AUDIO"]:
    st.file_uploader(
        f"Upload {'Image (JPG)' if step=='COVER' else 'Audio (WAV)'}", 
        key="uploaded_file", 
        on_change=handle_file_upload
    )

# 3. BUTTONS (Direct callbacks)
elif step == "COVER_FIX":
    c1, c2 = st.columns(2)
    c1.button("✨ Auto-Fix", on_click=handle_button_click, args=("FIX",), use_container_width=True)
    c2.button("Keep Original", on_click=handle_button_click, args=("SKIP",), use_container_width=True)

elif step == "RIGHTS":
    c1, c2 = st.columns(2)
    c1.button("It's a Cover", on_click=handle_button_click, args=("COVER",), use_container_width=True)
    c2.button("It's Original", on_click=handle_button_click, args=("ORIGINAL",), use_container_width=True)

elif step == "DONE":
    st.balloons()
