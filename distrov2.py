import streamlit as st
import time

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="DistroBot V10.3 (Editable)", page_icon="💿", layout="wide")

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
    
    /* Input Styling to blend with chat */
    .stTextInput > div > div > input {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE & NAVIGATION ---

def init_session():
    defaults = {
        "messages": [], # We will rebuild history dynamically based on state
        "step": "title",
        "user_data": {
            "Release Title": "",
            "Version": "Original",
            "Artist": "",
            "Type": "Original"
        },
        "cover_analyzed": False,
        "audio_processed": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# Navigation Helper
STEPS = ["title", "version", "artist", "cover", "cover_fix", "audio", "contributors", "finish"]

def go_to_step(step_name):
    st.session_state.step = step_name
    # Reset localized flags if moving back
    if step_name == "cover": 
        st.session_state.cover_analyzed = False
    if step_name == "audio": 
        st.session_state.audio_processed = False

# --- 3. SIDEBAR (VISION & CONTROLS) ---

with st.sidebar:
    st.title("🎛 Control Center")
    
    # --- NAVIGATION ---
    st.markdown("### 📍 Jump to Step")
    # Determine index safely
    try:
        current_idx = STEPS.index(st.session_state.step)
    except ValueError:
        current_idx = 0
        
    selected_step = st.radio("Edit / Navigate:", STEPS, index=current_idx, format_func=lambda x: x.replace("_", " ").title())
    
    if selected_step != st.session_state.step:
        go_to_step(selected_step)
        st.rerun()

    st.markdown("---")

    # --- VISION & LOGIC COMPONENT ---
    with st.expander("🚀 Project Vision & Architecture", expanded=True):
        st.markdown("""
        **What is this app?**
        This is an **AI-Powered A&R Agent** designed to solve the "Metadata Mess" in music distribution.
        
        **The Problem:** Artists upload "MySong_final_v3.mp3" with bad artwork. Spotify rejects it. The distributor loses money on support tickets.
        
        **The Solution (This Bot):**
        1.  **Guardrails (Logic):** It forces standard formatting (No "feat." in titles, specific Version fields).
        2.  **Vision Model (AI):** It "looks" at artwork to detect illegal text (Spotify rejects art with text).
        3.  **Audio Fingerprint (AI):** It listens to audio to detect copyright infringement (ACR Cloud) *before* distribution.
        
        **Technical Stack:**
        * **Frontend:** React / Streamlit (Prototype)
        * **Brain:** Google Gemini 2.5 Flash (Context aware)
        * **Validation:** Pydantic (Strict JSON Schema)
        """)

    with st.expander("📝 Data Payload (JSON)"):
        st.json(st.session_state.user_data)
        
    if st.button("🔴 Hard Reset"):
        st.session_state.clear()
        st.rerun()

# --- 4. CALLBACKS & LOGIC ---

def save_title():
    val = st.session_state.temp_title
    if val:
        st.session_state.user_data["Release Title"] = val
        go_to_step("version")

def save_artist():
    val = st.session_state.temp_artist
    if val:
        st.session_state.user_data["Artist"] = val
        go_to_step("cover")

def cb_analyze_cover():
    st.session_state.cover_analyzed = True

def cb_fix_cover_trigger():
    st.session_state.step = "cover_fix"
    st.session_state.cover_analyzed = False

def cb_approve_fix():
    st.session_state.step = "audio"

def cb_process_audio():
    st.session_state.audio_processed = True

def cb_type_cover():
    st.session_state.user_data["Type"] = "Cover"
    st.session_state.step = "contributors"
    st.session_state.audio_processed = False

def cb_type_original():
    st.session_state.user_data["Type"] = "Original"
    st.session_state.step = "contributors"
    st.session_state.audio_processed = False

# --- 5. RENDER CHAT FLOW ---

# HELPER: Render a chat bubble
def chat_bubble(role, text, source="System", model="Rule Engine"):
    with st.chat_message(role):
        st.markdown(text)
        if role == "assistant":
            badge = "badge-ai" if "AI" in source or "GPT" in model or "Vision" in source else "badge-logic"
            st.markdown(f"<div class='tech-badge {badge}'>⚙️ {source} &nbsp;|&nbsp; 🧠 {model}</div>", unsafe_allow_html=True)

# 1. TITLE STEP
if st.session_state.step == "title":
    chat_bubble("assistant", "Hello! Let's start. What is the **Release Title**?", "Init", "Hardcoded")
    
    # EDITABLE INPUT: We use text_input with 'value' pre-filled from history
    st.text_input("Track Title", 
                  value=st.session_state.user_data.get("Release Title", ""), 
                  key="temp_title", 
                  placeholder="e.g. Midnight Rain")
    
    st.button("Next ➝", on_click=save_title)

# 2. VERSION STEP
elif st.session_state.step == "version":
    # Show previous context
    chat_bubble("user", f"Title: {st.session_state.user_data.get('Release Title')}")
    chat_bubble("assistant", "Got it. Now, what is the **Version**?", "Logic", "Flow Control")
    
    col1, col2 = st.columns([2,1])
    with col1:
        v_select = st.selectbox("Version Type", 
            ["Original", "Alternate Take", "Instrumental", "Radio Edit", "Remastered", "Remix", "Other"],
            index=0) # You could calculate index to pre-fill if needed
            
    # Conditional logic
    if v_select == "Remix":
        st.checkbox("I confirm I have rights to this remix.", key="remix_confirm")
    elif v_select == "Other":
        st.text_input("Specify Version", key="other_ver")
    
    def next_version():
        # Logic to save
        final = v_select
        if v_select == "Other": final = st.session_state.other_ver
        st.session_state.user_data["Version"] = final
        go_to_step("artist")

    st.button("Next ➝", on_click=next_version)

# 3. ARTIST STEP
elif st.session_state.step == "artist":
    chat_bubble("user", f"Version: {st.session_state.user_data.get('Version')}")
    chat_bubble("assistant", "Who is the **Primary Artist**?", "Logic", "Flow Control")
    
    st.text_input("Artist Name", 
                  value=st.session_state.user_data.get("Artist", ""), 
                  key="temp_artist")
    
    st.button("Next ➝", on_click=save_artist)

# 4. COVER ART STEP
elif st.session_state.step == "cover":
    chat_bubble("user", f"Artist: {st.session_state.user_data.get('Artist')}")
    chat_bubble("assistant", "Please upload your **Cover Art**.", "Logic", "Asset Handler")
    
    uploaded = st.file_uploader("3000x3000px JPG/PNG", key="u_cover")
    
    if uploaded:
        st.session_state.cover_image = uploaded
        st.image(uploaded, width=250, caption="User Upload")
        
        if not st.session_state.cover_analyzed:
            st.button("🔍 Analyze Art", on_click=cb_analyze_cover)
        else:
            chat_bubble("assistant", "⚠️ **Issue Detected:** Text found ('Listen on Spotify').\nDSP stores reject art with marketing text.", "Vision Model", "Gemini Pro Vision")
            st.button("✨ Auto-Fix (AI Remove Text)", on_click=cb_fix_cover_trigger)

# 5. COVER FIX STEP
elif st.session_state.step == "cover_fix":
    chat_bubble("assistant", "Here is the cleaned artwork:", "Generative AI", "Inpainting")
    
    c1, c2 = st.columns(2)
    if "cover_image" in st.session_state:
        c1.image(st.session_state.cover_image, caption="Original")
        c2.image(st.session_state.cover_image, caption="✨ Cleaned (Simulated)")
    
    st.button("✅ Approve & Continue", on_click=cb_approve_fix)

# 6. AUDIO STEP
elif st.session_state.step == "audio":
    chat_bubble("assistant", "Artwork approved. Upload **Audio File**.", "Logic", "Asset Handler")
    
    aud = st.file_uploader("WAV / MP3", key="u_audio")
    if aud:
        if not st.session_state.audio_processed:
            st.button("🎧 Scan Audio", on_click=cb_process_audio)
        else:
            chat_bubble("assistant", "⚠️ **Copyright Match:** 'Shape of You' (Ed Sheeran).", "ACR Cloud", "Fingerprinting")
            st.write("Is this a Cover or Original?")
            c1, c2 = st.columns(2)
            c1.button("It's a Cover", on_click=cb_type_cover)
            c2.button("It's Original", on_click=cb_type_original)

# 7. CONTRIBUTORS
elif st.session_state.step == "contributors":
    chat_bubble("assistant", "Almost done. Add **Contributors**.", "Logic", "Flow")
    
    with st.form("contrib_form"):
        c_name = st.text_input("Name")
        c_role = st.selectbox("Role", ["Producer", "Writer", "Featured"])
        if st.form_submit_button("Add"):
            st.success(f"Added {c_name} as {c_role}")
            
    st.markdown("---")
    if st.button("🚀 Finish & Release"):
        go_to_step("finish")
        st.rerun()

# 8. FINISH
elif st.session_state.step == "finish":
    st.balloons()
    chat_bubble("assistant", "🎉 **Success!** Your release has been drafted.", "Backend", "API 200 OK")
    st.json(st.session_state.user_data)
    
    if st.button("Start New Release"):
        st.session_state.clear()
        st.rerun()
