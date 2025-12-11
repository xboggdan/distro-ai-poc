import streamlit as st
import time
import json

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="DistroBot Agent V2", page_icon="💿", layout="wide")

st.markdown("""
<style>
    /* Main Chat Container */
    .stChatMessage {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 15px;
        border: 1px solid #f0f2f6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    
    /* Technical Badges for AI Transparency */
    .tech-badge {
        font-size: 0.65em;
        font-weight: 600;
        letter-spacing: 0.5px;
        padding: 4px 8px;
        border-radius: 6px;
        margin-top: 8px;
        display: inline-block;
        font-family: 'Source Code Pro', monospace;
        border: 1px solid transparent;
        text-transform: uppercase;
    }
    
    /* Badge Variants */
    .badge-ai { background-color: #e3f2fd; color: #1565c0; border-color: #bbdefb; }
    .badge-logic { background-color: #f3e5f5; color: #7b1fa2; border-color: #e1bee7; }
    .badge-vision { background-color: #e8f5e9; color: #2e7d32; border-color: #c8e6c9; }
    .badge-audio { background-color: #fff3e0; color: #ef6c00; border-color: #ffe0b2; }

    /* Hide default Streamlit anchors */
    .st-emotion-cache-16idsys p { font-size: 16px; }
</style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE MANAGEMENT ---

def init_state():
    defaults = {
        "messages": [
            {"role": "assistant", "content": "👋 Hi, I'm **DistroBot**. I'm here to prepare your release for Spotify & Apple Music.\n\nLet's start. What is the **Title** of this track?", "badge": "System", "model": "Init"}
        ],
        "stage": "GET_TITLE",  # State Machine Tracker
        "user_data": {
            "Release Title": None,
            "Artist": None,
            "Type": "Original",
            "Calculated_Risk": "Low"
        },
        "temp_file": None
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_state()

# --- 3. HELPER FUNCTIONS ---

def add_message(role, content, badge=None, model=None):
    """Appends a message to the history."""
    st.session_state.messages.append({
        "role": role,
        "content": content,
        "badge": badge,
        "model": model
    })

def simulate_processing(seconds, text):
    """Visual feedback for 'Backend' work."""
    with st.spinner(text):
        time.sleep(seconds)

# --- 4. BACKEND LOGIC CONTROLLER (The Brain) ---

def handle_agent_logic(user_input, input_type="text"):
    """
    This function acts as the backend API. 
    It takes input, updates the JSON payload, and decides the next AI response.
    """
    current_stage = st.session_state.stage
    
    # --- STAGE 1: TITLE ---
    if current_stage == "GET_TITLE":
        st.session_state.user_data["Release Title"] = user_input
        add_message("user", user_input)
        
        # Logic: Check for "feat" in title (Common Metadata Error)
        if "feat" in user_input.lower():
            response = "I noticed you included 'feat' in the title. I've stripped that out for metadata compliance. Please add feature artists in the contributor section later."
            st.session_state.user_data["Release Title"] = user_input.split("feat")[0].strip()
            add_message("assistant", response, "Metadata Guardrail", "Regex Validator")
            
        add_message("assistant", f"Great. Title set to **{st.session_state.user_data['Release Title']}**.\n\nWho is the **Primary Artist**?", "Logic", "Flow Control")
        st.session_state.stage = "GET_ARTIST"

    # --- STAGE 2: ARTIST ---
    elif current_stage == "GET_ARTIST":
        st.session_state.user_data["Artist"] = user_input
        add_message("user", user_input)
        add_message("assistant", "Got it. Now, please upload your **Cover Art** (3000x3000px).", "Logic", "Asset Manager")
        st.session_state.stage = "UPLOAD_COVER"

    # --- STAGE 3: COVER ART PROCESS ---
    elif current_stage == "UPLOAD_COVER":
        # Input here is a file object
        add_message("user", "📁 Image Uploaded")
        
        simulate_processing(1.5, "🤖 Vision Model Scanning for text & nudity...")
        
        # Mock Vision API Result
        detected_issues = True # Simulating an issue found
        
        if detected_issues:
            response = "⚠️ **Issue Detected:** I see text saying 'Available Now'.\n\nSpotify rejects artwork with marketing text. I can fix this using generative fill."
            add_message("assistant", response, "Vision AI", "Gemini Pro Vision")
            st.session_state.stage = "FIX_COVER"
        else:
            add_message("assistant", "Artwork looks clean! Moving to audio.", "Vision AI", "Gemini Pro Vision")
            st.session_state.stage = "UPLOAD_AUDIO"

    # --- STAGE 4: COVER FIX ---
    elif current_stage == "FIX_COVER":
        if user_input == "FIX_IT":
            add_message("user", "✨ Yes, fix it automatically.")
            simulate_processing(2, "🎨 In-painting image...")
            add_message("assistant", "Fixed! Here is the clean version without text. Proceeding to Audio.", "Gen AI", "Stable Diffusion")
            st.session_state.stage = "UPLOAD_AUDIO"
        else:
            add_message("user", "Keep original.")
            st.session_state.stage = "UPLOAD_AUDIO"

    # --- STAGE 5: AUDIO PROCESS ---
    elif current_stage == "UPLOAD_AUDIO":
        add_message("user", "🎵 Audio Uploaded")
        simulate_processing(2, "🎧 Fingerprinting Audio (ACR Cloud)...")
        
        # Mock Audio Match
        add_message("assistant", "⚠️ **Copyright Warning:** This sounds like 'Shape of You' by Ed Sheeran.\n\nIs this a **Cover** or a **Remix**?", "Audio Analysis", "ACR Cloud")
        st.session_state.stage = "DEFINE_TYPE"

    # --- STAGE 6: DEFINE TYPE ---
    elif current_stage == "DEFINE_TYPE":
        st.session_state.user_data["Type"] = user_input
        add_message("user", user_input)
        
        final_msg = "Perfect. I've marked this as a **Cover**. Licensing requires a mechanical license (Harry Fox Agency)."
        add_message("assistant", final_msg, "Legal Logic", "Compliance Engine")
        
        add_message("assistant", "✅ **Release Drafted Successfully!** View the payload in the sidebar.", "System", "Complete")
        st.session_state.stage = "FINISHED"

    st.rerun()

# --- 5. UI LAYOUT & RENDERING ---

# A. Sidebar (The "Under the Hood" View)
with st.sidebar:
    st.title("🎛 Backend State")
    st.markdown("---")
    st.success(f"**Current Stage:** `{st.session_state.stage}`")
    
    with st.expander("📝 Live JSON Payload", expanded=True):
        st.json(st.session_state.user_data)
        
    st.markdown("### 🧠 Active Models")
    st.caption("• Gemini 1.5 Pro (Language)")
    st.caption("• Gemini Vision (OCR/Guardrails)")
    st.caption("• ACR Cloud (Audio Fingerprinting)")
    
    if st.button("Reset Conversation"):
        st.session_state.clear()
        st.rerun()

# B. Main Chat History Render
st.title("DistroBot Agent")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Render the Tech Badge if it exists
        if msg.get("badge"):
            b_class = "badge-logic"
            if "Vision" in msg["badge"]: b_class = "badge-vision"
            elif "Audio" in msg["badge"]: b_class = "badge-audio"
            elif "Gen" in msg["badge"]: b_class = "badge-ai"
            
            st.markdown(f"""
                <div class='tech-badge {b_class}'>
                    ⚙️ {msg['badge']} &nbsp;|&nbsp; ⚡ {msg['model']}
                </div>
            """, unsafe_allow_html=True)

# C. Dynamic Input Area (Context-Aware)
st.markdown("---")

# 1. TEXT INPUT SCENARIO
if st.session_state.stage in ["GET_TITLE", "GET_ARTIST"]:
    user_input = st.chat_input(f"Type {st.session_state.stage.replace('GET_', '').lower()} here...")
    if user_input:
        handle_agent_logic(user_input)

# 2. FILE UPLOAD SCENARIO (Images)
elif st.session_state.stage == "UPLOAD_COVER":
    with st.chat_message("assistant"):
        st.write("waiting for upload...")
        up_file = st.file_uploader("Upload Cover Art", type=["jpg", "png"], label_visibility="collapsed")
        if up_file:
            handle_agent_logic(up_file, input_type="file")

# 3. BUTTON/CHOICE SCENARIO (Fix Cover)
elif st.session_state.stage == "FIX_COVER":
    col1, col2 = st.columns(2)
    if col1.button("✨ Auto-Fix Art", use_container_width=True):
        handle_agent_logic("FIX_IT", input_type="button")
    if col2.button("Skip Fix", use_container_width=True):
        handle_agent_logic("SKIP", input_type="button")

# 4. FILE UPLOAD SCENARIO (Audio)
elif st.session_state.stage == "UPLOAD_AUDIO":
    with st.chat_message("assistant"):
        st.write("waiting for audio...")
        up_file = st.file_uploader("Upload Audio (WAV/MP3)", type=["wav", "mp3"], label_visibility="collapsed")
        if up_file:
            handle_agent_logic(up_file, input_type="file")

# 5. SELECTION SCENARIO (Copyright Type)
elif st.session_state.stage == "DEFINE_TYPE":
    col1, col2 = st.columns(2)
    if col1.button("It's a Cover", use_container_width=True):
        handle_agent_logic("Cover", input_type="button")
    if col2.button("It's Original", use_container_width=True):
        handle_agent_logic("Original", input_type="button")

# 6. FINISHED SCENARIO
elif st.session_state.stage == "FINISHED":
    st.balloons()
    if st.button("Start New Release"):
        st.session_state.clear()
        st.rerun()
