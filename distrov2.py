import streamlit as st
import time
import random

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="DistroBot V10.2 (Stable)", page_icon="💿", layout="wide")

st.markdown("""
<style>
    .stChatMessage {
        background-color: #f9f9f9;
        border-radius: 15px;
        padding: 10px;
        border: 1px solid #eee;
    }
    .tech-badge {
        font-size: 0.7em;
        color: #555;
        background-color: #e0e0e0;
        padding: 2px 8px;
        border-radius: 10px;
        margin-top: 6px;
        display: inline-block;
        font-family: monospace;
        border: 1px solid #ccc;
    }
    .badge-ai { background-color: #e3f2fd; color: #0d47a1; border-color: #90caf9; }
    .badge-logic { background-color: #fff3e0; color: #e65100; border-color: #ffcc80; }
    
    /* Highlight the active step */
    .step-highlight {
        border-left: 5px solid #FF4B4B;
        padding-left: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE MANAGEMENT (The Memory) ---

def init_session():
    defaults = {
        "messages": [{
            "role": "assistant", 
            "content": "Hello! I'm DistroBot V10. Let's get your music on Spotify. What is the **Release Title**?",
            "source": "Backend Logic",
            "model": "Hardcoded Init"
        }],
        "step": "title",           # Current Step: title, version, artist, cover, cover_fix, audio, contributors, finish
        "user_data": {},           # The JSON data we are building
        "mode": "Distribution Flow",
        
        # Sub-states (Flags to prevent UI resetting)
        "cover_analyzed": False,
        "audio_processed": False,
        "temp_title": "",          # Store inputs before confirming
        "temp_artist": ""
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# --- 3. LOGIC HANDLERS (CALLBACKS) ---
# These functions run BEFORE the UI reloads, guaranteeing the state is saved.

def add_message(role, content, source="User Input", model="N/A"):
    st.session_state.messages.append({
        "role": role, 
        "content": content, 
        "source": source, 
        "model": model
    })

def handle_title_submit():
    # 1. Get input
    user_input = st.session_state.title_input_widget
    if not user_input: return

    # 2. Add User Message
    add_message("user", user_input)
    
    # 3. Simulate AI Extraction
    triggers = ["my title is", "release title is", "name is", "called", "track is"]
    cleaned = user_input
    source, model = "Direct Input", "Rule-Engine v2"
    
    lower_input = user_input.lower()
    for trigger in triggers:
        if trigger in lower_input:
            start_index = lower_input.find(trigger) + len(trigger)
            cleaned = user_input[start_index:].strip().strip('".')
            source, model = "NLP Entity Extraction", "GPT-4o-Mini (Simulated)"
            break
            
    # 4. Update Data & State
    st.session_state.user_data["Release Title"] = cleaned
    
    # 5. Add AI Response
    add_message("assistant", f"Got it. Title set to: **'{cleaned}'**.", source=source, model=model)
    
    # 6. Move to next step
    st.session_state.step = "version"
    st.session_state.title_input_widget = "" # Clear input

def handle_version_confirm():
    # Logic is handled in the render loop for dropdowns, but we use this to transition
    v_type = st.session_state.v_select
    final_ver = v_type
    valid = True
    
    # Validation
    if v_type == "Remix" and not st.session_state.get("remix_check"):
        st.toast("❌ You must confirm remix rights!") 
        valid = False
    elif v_type == "Other":
        custom = st.session_state.get("other_input_widget")
        if not custom:
            st.toast("❌ Please specify the version.")
            valid = False
        else:
            final_ver = custom

    if valid:
        st.session_state.user_data["Version"] = final_ver
        add_message("assistant", f"Version Type saved: **{final_ver}**", source="Validation Logic", model="Rule-Engine v1")
        add_message("assistant", "Who is the **Primary Artist**?", source="Flow Controller", model="Hardcoded")
        st.session_state.step = "artist"

def handle_artist_submit():
    user_input = st.session_state.artist_input_widget
    if user_input:
        add_message("user", user_input)
        st.session_state.user_data["Artist"] = user_input
        add_message("assistant", f"Artist set to **{user_input}**. Upload **Cover Art**.", source="Backend Logic", model="N/A")
        st.session_state.step = "cover"
        st.session_state.artist_input_widget = ""

# --- CRITICAL FIX FOR COVER ART ---
def cb_analyze_cover():
    """Triggered when user clicks 'Analyze'"""
    st.session_state.cover_analyzed = True
    # We do NOT move the step yet. We stay on 'cover' but show more UI.

def cb_apply_fix():
    """Triggered when user clicks 'Auto-Fix'"""
    st.session_state.step = "cover_fix"
    st.session_state.cover_analyzed = False # Reset for future

def cb_confirm_fixed_art():
    add_message("assistant", "Art fixed and approved. Upload **Audio**.", source="Vision Pipeline", model="DALL-E 3 / Inpainting")
    st.session_state.step = "audio"

# --- CRITICAL FIX FOR AUDIO ---
def cb_process_audio():
    st.session_state.audio_processed = True

def cb_is_cover():
    st.session_state.user_data["Type"] = "Cover"
    add_message("assistant", "Marked as Cover. Any contributors?", source="ACR Cloud API", model="Audio Fingerprinting")
    st.session_state.step = "contributors"
    st.session_state.audio_processed = False

def cb_is_original():
    st.session_state.user_data["Type"] = "Original"
    add_message("assistant", "Marked as Original. Any contributors?", source="User Input", model="N/A")
    st.session_state.step = "contributors"
    st.session_state.audio_processed = False

# --- 4. MAIN RENDER LOOP ---

# Sidebar
with st.sidebar:
    st.title("🎛 Control Center")
    if st.button("🔴 Hard Reset"):
        st.session_state.clear()
        st.rerun()
    with st.expander("Debugger"):
        st.write(f"**Current Step:** {st.session_state.step}")
        st.write(f"**Analyzed:** {st.session_state.cover_analyzed}")
        st.json(st.session_state.user_data)

# Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        source = msg.get("source", "Legacy")
        model = msg.get("model", "N/A")
        if msg["role"] == "assistant":
            badge_class = "badge-ai" if "GPT" in model or "RAG" in source else "badge-logic"
            st.markdown(f"<div class='tech-badge {badge_class}'>⚙️ {source} &nbsp;|&nbsp; 🧠 {model}</div>", unsafe_allow_html=True)

# --- INTERACTIVE STEPS ---

# 1. TITLE
if st.session_state.step == "title":
    st.chat_input("Enter release title...", key="title_input_widget", on_submit=handle_title_submit)

# 2. VERSION
elif st.session_state.step == "version":
    with st.container():
        st.info("👇 Select Version Details")
        col1, col2 = st.columns([2,1])
        with col1:
            st.selectbox("Version Type", 
                ["Original", "Alternate Take", "Instrumental", "Radio Edit", "Remastered", "Remix", "Other"], 
                key="v_select")
        
        # Conditional UI rendering
        if st.session_state.v_select == "Remix":
            st.checkbox("I confirm I have rights.", key="remix_check")
        elif st.session_state.v_select == "Other":
            st.text_input("Specify Version", key="other_input_widget")
        elif st.session_state.v_select == "Remastered":
             st.number_input("Year", 1900, 2025)

        st.button("Confirm Version", on_click=handle_version_confirm)

# 3. ARTIST
elif st.session_state.step == "artist":
    st.chat_input("Enter Artist Name...", key="artist_input_widget", on_submit=handle_artist_submit)

# 4. COVER ART (THE FIXED SECTION)
elif st.session_state.step == "cover":
    uploaded_file = st.file_uploader("Upload Art (3000x3000px)", type=['jpg', 'png'], key="cover_uploader")
    
    if uploaded_file:
        st.session_state.cover_image = uploaded_file # Save explicitly
        st.image(uploaded_file, width=250, caption="Preview")
        
        # UI BRANCHING based on state
        if not st.session_state.cover_analyzed:
            # STATE A: File uploaded, waiting for analysis
            st.button("Analyze & Upload", on_click=cb_analyze_cover)
        
        else:
            # STATE B: Analyzed, showing results and waiting for action
            st.warning("⚠️ Text Detected: 'Listen on Spotify'")
            st.info("💡 Recommendation: Use AI to remove marketing text.")
            
            # This button triggers the callback to move to next step
            st.button("✨ Auto-Fix (AI)", on_click=cb_apply_fix)

# 5. COVER FIX VIEW
elif st.session_state.step == "cover_fix":
    c1, c2 = st.columns(2)
    if "cover_image" in st.session_state:
        c1.image(st.session_state.cover_image, caption="Original")
        c2.image(st.session_state.cover_image, caption="✨ AI Fixed (Simulated)", output_format="JPEG")
    
    st.button("Use Fixed Artwork", on_click=cb_confirm_fixed_art)

# 6. AUDIO (THE FIXED SECTION)
elif st.session_state.step == "audio":
    audio = st.file_uploader("Upload WAV/MP3", type=['wav', 'mp3'], key="audio_uploader")
    
    if audio:
        if not st.session_state.audio_processed:
            st.button("Process Audio", on_click=cb_process_audio)
        else:
            st.error("⚠️ ACR Match: 'Shape of You' detected.")
            st.write("Is this a cover?")
            c1, c2 = st.columns(2)
            c1.button("Yes, Cover", on_click=cb_is_cover)
            c2.button("No, Original", on_click=cb_is_original)

# 7. CONTRIBUTORS
elif st.session_state.step == "contributors":
    st.write("### Add Contributors")
    c_name = st.text_input("Contributor Name")
    c_role = st.multiselect("Role", ["Featured Artist", "Producer", "Lyricist", "Composer"])
    
    if st.button("Add Contributor"):
        if c_name: st.success(f"Added {c_name}")
        
    st.markdown("---")
    if st.button("Finish Release"):
        st.session_state.step = "finish"
        st.rerun()

# 8. FINISH
elif st.session_state.step == "finish":
    st.balloons()
    st.success("Release Ready for Distribution!")
    st.json(st.session_state.user_data)
    if st.button("Start Over"):
        st.session_state.clear()
        st.rerun()
