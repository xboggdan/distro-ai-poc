import streamlit as st
import time
import re

# --- 1. SETUP & STYLING ---
st.set_page_config(page_title="DistroBot Academy", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #FAFAFA; color: #1a1a1a; }
    .stChatMessage {
        background-color: #FFFFFF; border: 1px solid #E0E0E0;
        border-radius: 12px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    }
    /* Tech Badges */
    .logic-badge {
        font-size: 0.7em; padding: 4px 8px; border-radius: 6px;
        background-color: #e3f2fd; color: #1565c0; border: 1px solid #bbdefb;
        display: inline-block; margin-top: 8px; font-weight: 600; font-family: monospace;
    }
    .badge-alert { background-color: #ffebee; color: #c62828; border-color: #ffcdd2; }
    
    /* Sidebar Education Box */
    .edu-box {
        background-color: #F0F4F8; border-left: 4px solid #0078D4;
        padding: 15px; border-radius: 4px; margin-bottom: 20px; font-size: 0.9em;
    }
    .edu-title { font-weight: bold; color: #0078D4; margin-bottom: 5px; }
    
    /* Preview Card */
    .preview-card {
        border: 1px solid #eee; border-radius: 16px; overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08); background: white;
    }
    .preview-img { width: 100%; height: 250px; background-size: cover; background-position: center; background-color: #eee; }
    .preview-content { padding: 15px; }
</style>
""", unsafe_allow_html=True)

# --- 2. STATE & DATA ---

def init_state():
    defaults = {
        "history": [{
            "role": "assistant", 
            "content": "🎓 **Welcome to DistroBot.**\n\nI am your A&R Agent. I will guide you through the 7 steps required to distribute music to Spotify/Apple without rejection.\n\n**Step 1:** What is the **Release Title**?",
            "badge": "System Ready", "type": "info"
        }],
        "step": "TITLE",
        "payload": {
            "title": "", 
            "version": "Original",
            "artist": "", 
            "contributors": [],
            "explicit": "Clean",
            "is_cover": False
        },
        "temp_cover": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# --- 3. EDUCATIONAL CONTENT (The "Why") ---
# This dictionary maps steps to educational context
EDU_CONTENT = {
    "TITLE": {
        "title": " Why Formatting Matters?",
        "body": "DSPs (Digital Service Providers) like Spotify have strict style guides. **Titles cannot contain 'feat.' or producer tags.** This ensures the metadata is readable across all devices."
    },
    "VERSION": {
        "title": "Version Handling",
        "body": "If this isn't the original recording, you must specify the version (e.g., 'Radio Edit', 'Remix'). This links the song correctly in the database to the original composition."
    },
    "ARTIST": {
        "title": "Primary vs. Featured",
        "body": "The Primary Artist is the main performer. Featured artists should be listed separately to ensure they map to the correct artist profiles on Apple Music."
    },
    "CONTRIBUTORS": {
        "title": "Credits & Publishing",
        "body": "Collecting societies need to know who wrote and produced the track. Missing this data means missing royalty payments."
    },
    "EXPLICIT": {
        "title": "Parental Advisory",
        "body": "Marking a song 'Explicit' adds the 'E' tag. Failing to mark explicit content correctly can lead to your release being hidden in 'Restricted Mode'."
    },
    "COVER": {
        "title": "Artwork Rules",
        "body": "Stores reject artwork with: URLs, contact info, blurred images, or pricing. Our Vision AI checks for these prohibited elements."
    },
    "AUDIO": {
        "title": "Audio Fingerprinting",
        "body": "We scan your audio against a database of 100M+ songs to detect unauthorized samples before copyright strikes happen."
    }
}

# --- 4. LOGIC ENGINE (CALLBACKS) ---

def add_msg(role, text, badge=None, b_type="normal"):
    st.session_state.history.append({"role": role, "content": text, "badge": badge, "type": b_type})

# A. TEXT HANDLER
def handle_text_input():
    val = st.session_state.user_input_widget
    if not val: return
    
    step = st.session_state.step
    p = st.session_state.payload

    if step == "TITLE":
        add_msg("user", val)
        # 1. Guardrail: Feat check
        if re.search(r"(?i)\bfeat\.?|\bft\.?", val):
            clean = re.sub(r"(?i)\s*\(?(feat\.?|ft\.?).*?\)?", "", val).strip()
            p['title'] = clean
            add_msg("assistant", f"I removed 'feat' to comply with Style Guide.\nTitle set to: **{clean}**", "Metadata Guardrail", "alert")
        else:
            p['title'] = val
            add_msg("assistant", f"Title set: **{val}**", "Logic Engine")
        
        add_msg("assistant", "Is this the **Original** version, or something else?", "Flow")
        st.session_state.step = "VERSION"

    elif step == "ARTIST":
        add_msg("user", val)
        p['artist'] = val
        add_msg("assistant", "Artist set. Now, list any **Contributors** (Producers/Writers). Type 'None' if finished.", "Flow")
        st.session_state.step = "CONTRIBUTORS"

    elif step == "CONTRIBUTORS":
        add_msg("user", val)
        if val.lower() == "none":
            add_msg("assistant", "Contributors saved. Is the track **Clean** or **Explicit**?", "Flow")
            st.session_state.step = "EXPLICIT"
        else:
            p['contributors'].append(val)
            add_msg("assistant", f"Added **{val}**. Add another or type 'None'.", "Database Update")

# B. BUTTON HANDLER (For Version, Explicit, Rights)
def handle_choice(key, value, next_step, next_msg_user, next_msg_bot):
    if key: st.session_state.payload[key] = value
    add_msg("user", next_msg_user)
    add_msg("assistant", next_msg_bot, "Logic Engine")
    st.session_state.step = next_step

# C. FILE HANDLER
def handle_file():
    f = st.session_state.u_file
    if not f: return
    step = st.session_state.step
    
    if step == "COVER":
        add_msg("user", "📁 Cover Uploaded")
        st.session_state.temp_cover = True
        with st.spinner("🧠 Vision AI scanning for text/nudity..."):
            time.sleep(1)
        add_msg("assistant", "✅ **Artwork Approved.** No illegal text found.\n\nNow upload **Master Audio**.", "Gemini Vision", "success")
        st.session_state.step = "AUDIO"

    elif step == "AUDIO":
        add_msg("user", "🎵 Audio Uploaded")
        with st.spinner("🎧 Checking Copyright..."):
            time.sleep(1)
        add_msg("assistant", "⚠️ **Copyright Warning:** Sample detected from 'Shape of You'.\nIs this a **Cover**?", "ACR Cloud", "alert")
        st.session_state.step = "RIGHTS"

# --- 5. UI LAYOUT ---

# --- SIDEBAR (Preview & Education) ---
with st.sidebar:
    st.title("🎛 Control Center")
    
    # 1. DYNAMIC EDUCATION BOX
    current_edu = EDU_CONTENT.get(st.session_state.step, {})
    if current_edu:
        st.markdown(f"""
        <div class="edu-box">
            <div class="edu-title">💡 {current_edu['title']}</div>
            {current_edu['body']}
        </div>
        """, unsafe_allow_html=True)
    
    # 2. LIVE PREVIEW
    p = st.session_state.payload
