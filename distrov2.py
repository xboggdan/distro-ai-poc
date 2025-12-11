import streamlit as st
import time

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="BandLab Distribution Agent", page_icon="🎸", layout="wide")

# --- 2. BANDLAB BRANDING & CUSTOM CSS (The "Index.html" styling) ---
st.markdown("""
<style>
    /* BANDLAB COLOR PALETTE: #F50000 (Red), #1A1A1A (Dark BG), #FFFFFF (Text) */
    
    /* Main Background */
    .stApp {
        background-color: #121212;
        color: white;
    }

    /* Chat Messages */
    .stChatMessage {
        background-color: #1E1E1E;
        border: 1px solid #333;
        border-radius: 12px;
    }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #262626; /* Slightly lighter for contrast */
    }

    /* Input Fields */
    .stTextInput > div > div > input {
        background-color: #333;
        color: white;
        border: 1px solid #555;
        border-radius: 8px;
    }
    
    /* Buttons (The BandLab Red) */
    .stButton > button {
        background-color: #F50000;
        color: white;
        border: none;
        border-radius: 20px;
        padding: 10px 24px;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #CC0000;
        color: white;
        box-shadow: 0 4px 12px rgba(245, 0, 0, 0.4);
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #000000;
        border-right: 1px solid #333;
    }

    /* Custom Release Card (The "Preview") */
    .release-card {
        background: linear-gradient(145deg, #1e1e1e, #141414);
        border: 1px solid #333;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        margin-bottom: 20px;
    }
    .release-art-placeholder {
        width: 100%;
        aspect-ratio: 1/1;
        background-color: #333;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #666;
        margin-bottom: 15px;
        border: 2px dashed #444;
    }
    .release-title { font-size: 1.2em; font-weight: bold; color: white; margin-bottom: 5px; }
    .release-artist { font-size: 0.9em; color: #F50000; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    .release-meta { font-size: 0.75em; color: #888; margin-top: 10px; }
    
    /* Tech Badges */
    .tech-badge {
        font-size: 0.6em;
        background: #333;
        color: #aaa;
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid #444;
        display: inline-block;
        margin-top: 5px;
        font-family: monospace;
    }
    .badge-highlight { border-color: #F50000; color: #fff; }

</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE ---
def init_state():
    defaults = {
        "messages": [
            {"role": "assistant", "content": "🎸 **Hey Creator.** I'm the BandLab Distribution Agent.\n\nLet's get your music on Spotify. What is the **Title** of your new track?", "badge": "System"}
        ],
        "stage": "GET_TITLE",
        "data": {
            "title": "Untitled Track",
            "artist": "Unknown Artist",
            "version": "Original",
            "type": "Single",
            "cover_status": "Pending",
            "audio_status": "Pending"
        }
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# --- 4. BACKEND LOGIC (The Brain) ---
def agent_reply(text, badge=None):
    st.session_state.messages.append({"role": "assistant", "content": text, "badge": badge})

def handle_input(user_val, input_type="text"):
    stage = st.session_state.stage
    
    # 1. TITLE
    if stage == "GET_TITLE":
        st.session_state.messages.append({"role": "user", "content": user_val})
        st.session_state.data["title"] = user_val
        agent_reply(f"Nice. **{user_val}** is a solid title.\n\nWho is the **Primary Artist**?", "Logic")
        st.session_state.stage = "GET_ARTIST"
        
    # 2. ARTIST
    elif stage == "GET_ARTIST":
        st.session_state.messages.append({"role": "user", "content": user_val})
        st.session_state.data["artist"] = user_val
        agent_reply("Got it. Now, upload your **Cover Art**.", "Logic")
        st.session_state.stage = "UPLOAD_COVER"
        
    # 3. COVER ART
    elif stage == "UPLOAD_COVER":
        # Simulating file processing
        st.session_state.data["cover_status"] = "Uploaded"
        with st.spinner("🤖 Vision AI Checking for offensive content..."):
            time.sleep(1.5)
            
        agent_reply("✅ **Artwork Approved.** No text or guidelines violations found.\n\nNow, upload your **Master Audio** (WAV).", "Gemini Vision")
        st.session_state.stage = "UPLOAD_AUDIO"
        
    # 4. AUDIO
    elif stage == "UPLOAD_AUDIO":
        st.session_state.data["audio_status"] = "Uploaded"
        with st.spinner("🎧 Scanning audio fingerprint..."):
            time.sleep(2)
            
        agent_reply("⚠️ **Wait.** ACR Cloud detected a match for *'Sample_01.wav'*.\n\nIs this loop cleared or is this a **Cover Song**?", "ACR Cloud")
        st.session_state.stage = "CHECK_RIGHTS"
        
    # 5. RIGHTS
    elif stage == "CHECK_RIGHTS":
        if user_val == "Cover":
            st.session_state.messages.append({"role": "user", "content": "It is a Cover Song"})
            st.session_state.data["type"] = "Cover"
            agent_reply("Understood. We will flag this for Mechanical Licensing.\n\n**Release Ready.** Check the preview card.", "Legal Engine")
        else:
            st.session_state.messages.append({"role": "user", "content": "Samples are cleared"})
            st.session_state.data["type"] = "Original"
            agent_reply("Perfect. Marking as Original Composition.\n\n**Release Ready.** Check the preview card.", "Legal Engine")
            
        st.session_state.stage = "FINISHED"

# --- 5. SIDEBAR: THE LIVE PREVIEW (Replacing Index.html) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/BandLab_Technologies_logo.svg/2560px-BandLab_Technologies_logo.svg.png", width=150)
    st.markdown("### 📀 Release Preview")
    st.caption("This updates live as you chat.")
    
    # DYNAMIC HTML CARD
    d = st.session_state.data
    
    # Determine Cover Art Display
    cover_html = '<div class="release-art-placeholder"><span>No Art</span></div>'
    if d["cover_status"] == "Uploaded":
        # Using a placeholder image for demo, in real app use base64 of uploaded file
        cover_html = f'<img src="https://images.unsplash.com/photo-1614613535308-eb5fbd3d2c17?q=80&w=1000&auto=format&fit=crop" style="width:100%; border-radius:8px; margin-bottom:15px;">'

    st.markdown(f"""
    <div class="release-card">
        {cover_html}
        <div class="release-title">{d['title']}</div>
        <div class="release-artist">{d['artist']}</div>
        <div class="release-meta">
            {d['version']} • {d['type']} <br>
            Audio: {d['audio_status']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.stage == "FINISHED":
        st.success("✨ Ready for Distribution")
        st.button("🚀 Distribute to Spotify")
    
    st.divider()
    if st.button("Start Over"):
        st.session_state.clear()
        st.rerun()

# --- 6. MAIN CHAT INTERFACE ---

st.title("Distribution Assistant")

# Render History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("badge"):
            hl = "badge-highlight" if "Vision" in msg["badge"] or "Cloud" in msg["badge"] else ""
            st.markdown(f"<span class='tech-badge {hl}'>{msg['badge']}</span>", unsafe_allow_html=True)

# Dynamic Input Zone
st.markdown("---")
stage = st.session_state.stage

if stage in ["GET_TITLE", "GET_ARTIST"]:
    txt = st.chat_input("Type here...")
    if txt: handle_input(txt)

elif stage == "UPLOAD_COVER":
    with st.chat_message("assistant"):
        st.write("Waiting for JPG/PNG...")
        f = st.file_uploader("Cover Art", type=["jpg", "png"], label_visibility="collapsed")
        if f: handle_input(f, "file")

elif stage == "UPLOAD_AUDIO":
    with st.chat_message("assistant"):
        st.write("Waiting for WAV...")
        f = st.file_uploader("Master Audio", type=["wav"], label_visibility="collapsed")
        if f: handle_input(f, "file")
        
elif stage == "CHECK_RIGHTS":
    col1, col2 = st.columns(2)
    if col1.button("It's a Cover"): handle_input("Cover", "btn")
    if col2.button("Samples Cleared"): handle_input("Original", "btn")
    
elif stage == "FINISHED":
    st.balloons()
