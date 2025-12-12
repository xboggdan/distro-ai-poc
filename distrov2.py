import streamlit as st
import time
import re

# --- 1. CONFIGURATION & BANDLAB STYLING ---
st.set_page_config(page_title="BandLab DistroBot", page_icon="🔥", layout="wide")

st.markdown("""
<style>
    /* BANDLAB THEME: Clean White, Dark Text, Red Accents */
    .stApp { background-color: #ffffff; color: #222; }
    
    /* Chat Bubbles */
    .stChatMessage {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #fff;
        border-color: #eee;
    }

    /* Primary Button (BandLab Red) */
    .stButton > button {
        background-color: #F50000;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 8px 24px;
        font-weight: 600;
        transition: 0.3s;
    }
    .stButton > button:hover { background-color: #c90000; color: white; }

    /* Secondary/Ghost Button */
    .secondary-btn {
        background-color: transparent;
        border: 1px solid #ddd;
        color: #333;
    }

    /* Review Card Styling */
    .review-section {
        border-bottom: 1px solid #eee;
        padding: 10px 0;
    }
    .review-label { font-size: 0.8em; color: #666; text-transform: uppercase; }
    .review-val { font-weight: 600; font-size: 1.0em; color: #000; }
    
    /* Education Box */
    .edu-box {
        background-color: #FFF3E0;
        border-left: 4px solid #FF9800;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 4px;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA MODEL & STATE ---

def init_state():
    defaults = {
        "history": [{
            "role": "assistant", 
            "content": "🔥 **Welcome to BandLab Distribution.**\n\nI will guide you through the 4-step process to get your music on Spotify & Apple Music.\n\n**Step 1: Release Details**\nLet's start. What is the **Release Title** (Album/Single name)?",
            "type": "init"
        }],
        "step": "S1_TITLE", # State Machine Tracker
        "edu_mode": False,  # Education Toggle
        "editing": False,   # Flag for "Review & Edit" mode
        # --- THE FULL PAYLOAD (Mapped from Screenshots) ---
        "data": {
            # STEP 1: Release Info
            "release_title": "",
            "release_version": "",
            "main_artist": "xboggdan", # Pre-filled from profile (simulated)
            "genre": "",
            "upc": "", # Optional
            "release_date_mode": "ASAP", # ASAP or Specific
            "release_date": None,
            "label": "", # Optional
            
            # STEP 2: Track Details
            "track_title": "",
            "track_version": "",
            "composers": [], # List of names
            "artists": [],   # List of dicts {name, role}
            "performers": [],
            "producers": [],
            "contributors": [],
            "released_before": False,
            "lyrics_type": "Instrumental", # Instrumental / English / etc
            "explicit": "Clean",
            "lyricists": [],
            "isrc": "",
            "publisher": "",
            "audio_file": None,
            
            # STEP 3: Assets
            "cover_art": None
        }
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# --- 3. KNOWLEDGE BASE (For Education Toggle) ---
KB = {
    "UPC": "Universal Product Code. It identifies the product (album/single). If you don't have one, BandLab generates it for free.",
    "ISRC": "International Standard Recording Code. It identifies the specific recording. Essential for tracking royalties.",
    "Composers": "Legal names are required here (e.g., 'John Smith', not 'Lil J'). This ensures the actual songwriter gets paid publishing royalties.",
    "Explicit": "You must mark 'Explicit' if there is strong language, violence, or drug references. Failure to do so can get your release hidden by parental controls.",
    "Cover Art": "Must be 3000x3000px. No URLs, social handles, or blurry images. DSPs are very strict about this.",
    "Label": "If you are independent, you can use your artist name or a custom label name here. e.g., 'Dreamwave Records'."
}

# --- 4. LOGIC ENGINE ---

def add_msg(role, text):
    st.session_state.history.append({"role": role, "content": text})

def get_next_step(current):
    # This defines the linear flow
    flow = [
        "S1_TITLE", "S1_VERSION", "S1_GENRE", "S1_DATE", "S1_LABEL", "S1_UPC",
        "S2_TITLE", "S2_VERSION", "S2_COMPOSERS", "S2_ARTISTS", "S2_PERFORMERS", 
        "S2_PRODUCERS", "S2_CONTRIB", "S2_BEFORE", "S2_LYRICS_TYPE", 
        "S2_LYRICISTS", "S2_EXPLICIT", "S2_ISRC", "S2_PUBLISHER", "S2_AUDIO",
        "S3_COVER", "S4_REVIEW", "SUBMITTED"
    ]
    try:
        idx = flow.index(current)
        return flow[idx+1]
    except:
        return "S4_REVIEW"

def process_input(user_input, input_type="text"):
    """
    The Core Brain. Updates state, validates data, and determines the next question.
    """
    step = st.session_state.step
    data = st.session_state.data
    
    # 1. HANDLE EDIT MODE (Jump back to Review after 1 change)
    if st.session_state.editing:
        # Save specific field based on step
        if step == "S1_TITLE": data["release_title"] = user_input
        elif step == "S1_GENRE": data["genre"] = user_input
        # ... (Add mapping for all fields)
        
        st.session_state.editing = False
        st.session_state.step = "S4_REVIEW"
        add_msg("assistant", "✅ Updated. Returning to review.")
        return

    # 2. NORMAL FLOW
    
    # --- STEP 1: RELEASE ---
    if step == "S1_TITLE":
        data["release_title"] = user_input
        add_msg("user", user_input)
        add_msg("assistant", f"Release Title: **{user_input}**. Any specific **Version**? (e.g., Deluxe, Remastered). Type 'None' to skip.")
        st.session_state.step = "S1_VERSION"

    elif step == "S1_VERSION":
        add_msg("user", user_input)
        if user_input.lower() != "none": data["release_version"] = user_input
        add_msg("assistant", "Select your **Genre**.")
        st.session_state.step = "S1_GENRE"

    elif step == "S1_GENRE":
        # Handled by buttons below, but if text:
        data["genre"] = user_input
        add_msg("user", user_input)
        add_msg("assistant", "When should this go live? (ASAP / Specific Date)")
        st.session_state.step = "S1_DATE"

    elif step == "S1_DATE":
        add_msg("user", user_input)
        if "specific" in user_input.lower():
            add_msg("assistant", "Please enter the date (YYYY-MM-DD).")
            # Logic would pause here for date, simplifying for demo:
        data["release_date_mode"] = user_input
        add_msg("assistant", "Record **Label** name? (Optional - Type 'None' to use default).")
        st.session_state.step = "S1_LABEL"

    elif step == "S1_LABEL":
        add_msg("user", user_input)
        if user_input.lower() != "none": data["label"] = user_input
        add_msg("assistant", "Do you have a **UPC**? (12/13 digits). Type 'None' if you want us to generate one.")
        st.session_state.step = "S1_UPC"

    elif step == "S1_UPC":
        add_msg("user", user_input)
        if user_input.lower() != "none":
            if not user_input.isdigit() or len(user_input) < 12:
                add_msg("assistant", "⚠️ Invalid UPC. Must be 12-13 digits. Try again or type 'None'.")
                return # Stop progression
            data["upc"] = user_input
        
        # TRANSITION TO STEP 2
        add_msg("assistant", "✅ Release details saved.\n\n**Step 2: Track Details**\nWhat is the **Track Title**?")
        st.session_state.step = "S2_TITLE"

    # --- STEP 2: TRACK ---
    elif step == "S2_TITLE":
        data["track_title"] = user_input
        add_msg("user", user_input)
        add_msg("assistant", "Track Version? (e.g., Radio Edit). Type 'None' to skip.")
        st.session_state.step = "S2_VERSION"

    elif step == "S2_VERSION":
        add_msg("user", user_input)
        if user_input.lower() != "none": data["track_version"] = user_input
        add_msg("assistant", "Adding **Composers**. Please enter the **Legal First & Last Name** (Required for publishing).")
        st.session_state.step = "S2_COMPOSERS"

    elif step == "S2_COMPOSERS":
        add_msg("user", user_input)
        # Validation
        if len(user_input.split()) < 2:
            add_msg("assistant", "⚠️ Legal name requires First and Last name (e.g., 'John Doe'). Please try again.")
            return
        
        data["composers"].append(user_input)
        add_msg("assistant", f"Added {user_input}. Add another? Type 'Next' to move on.")
        # Logic to stay in loop or move
        # For demo, assuming user hits "Next" button or types it
        
    elif step == "S2_LYRICS_TYPE":
        # Handled by buttons
        pass

    # ... (Skipping repetitive logic for brevity, but map assumes all fields exist) ...
    # We will jump straight to the tricky logic parts

    elif step == "S2_ISRC":
        add_msg("user", user_input)
        if user_input.lower() != "none": data["isrc"] = user_input
        add_msg("assistant", "Publisher? (Optional).")
        st.session_state.step = "S2_PUBLISHER"

    elif step == "S2_PUBLISHER":
        add_msg("user", user_input)
        if user_input.lower() != "none": data["publisher"] = user_input
        add_msg("assistant", "Please upload your **Audio File** (WAV/MP3).")
        st.session_state.step = "S2_AUDIO"

    # --- STEP 3: ASSETS ---
    elif step == "S2_AUDIO":
        # File handler calls this
        add_msg("assistant", "🎵 Audio received. Finally, **Step 3**: Upload **Cover Art** (3000x3000px).")
        st.session_state.step = "S3_COVER"
    
    elif step == "S3_COVER":
         add_msg("assistant", "🖼️ Art received. Generating Review...")
         st.session_state.step = "S4_REVIEW"

# --- 5. UI COMPONENTS ---

# Sidebar Education Toggle
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/BandLab_Technologies_logo.svg/2560px-BandLab_Technologies_logo.svg.png", width=150)
    st.markdown("### 🛠 Tools")
    st.session_state.edu_mode = st.toggle("🎓 Education Mode", value=False)
    
    if st.session_state.edu_mode:
        st.info("💡 **Education Mode On**\nI will explain what each field means as we go.")
    
    st.divider()
    
    # Live Preview Card
    d = st.session_state.data
    st.markdown("**Live Draft:**")
    st.markdown(f"""
    <div style="border:1px solid #ddd; padding:10px; border-radius:8px; text-align:center;">
        <div style="background:#eee; width:100%; height:150px; margin-bottom:5px; display:flex; align-items:center; justify-content:center;">
            { '🖼️ Art' if d['cover_art'] else 'Pending Art'}
        </div>
        <b>{d['release_title'] or 'Untitled Release'}</b><br>
        <span style="font-size:0.8em; color:#666;">{d['main_artist']}</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Reset Draft"):
        st.session_state.clear()
        st.rerun()

# --- 6. MAIN CHAT INTERFACE ---

st.title("Build Your Release")

# Display History
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Education Tip Injection
if st.session_state.edu_mode:
    # Find keyword match for current step
    tip_key = None
    if "UPC" in st.session_state.step: tip_key = "UPC"
    elif "ISRC" in st.session_state.step: tip_key = "ISRC"
    elif "COMPOSERS" in st.session_state.step: tip_key = "Composers"
    elif "COVER" in st.session_state.step: tip_key = "Cover Art"
    
    if tip_key:
        st.markdown(f"""<div class="edu-box">🎓 <b>BandLab Tips:</b> {KB[tip_key]}</div>""", unsafe_allow_html=True)

# --- 7. DYNAMIC INPUT AREAS ---

step = st.session_state.step
data = st.session_state.data

# A. SPECIAL REVIEW SCREEN (Step 4)
if step == "S4_REVIEW":
    st.divider()
    st.subheader("Review Release Details")
    st.caption("Click 'Edit' to change any field.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💿 Release Info")
        # Helper to make edit row
        def edit_row(label, val, step_id):
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"<div class='review-section'><div class='review-label'>{label}</div><div class='review-val'>{val or '-'}</div></div>", unsafe_allow_html=True)
            if c2.button("Edit", key=f"edit_{step_id}"):
                st.session_state.editing = True
                st.session_state.step = step_id
                add_msg("assistant", f"Okay, enter the new **{label}**:")
                st.rerun()

        edit_row("Release Title", data["release_title"], "S1_TITLE")
        edit_row("Version", data["release_version"], "S1_VERSION")
        edit_row("Genre", data["genre"], "S1_GENRE")
        edit_row("UPC", data["upc"], "S1_UPC")
        
    with col2:
        st.markdown("#### 🎵 Track Info")
        edit_row("Track Title", data["track_title"], "S2_TITLE")
        edit_row("Composers", ", ".join(data["composers"]), "S2_COMPOSERS")
        edit_row("Audio Status", "Uploaded" if data["audio_file"] else "Pending", "S2_AUDIO")
        edit_row("ISRC", data["isrc"], "S2_ISRC")

    st.markdown("---")
    if st.button("🚀 SUBMIT RELEASE", use_container_width=True):
        st.session_state.step = "SUBMITTED"
        st.balloons()
        add_msg("assistant", "🎉 **Success!** Your release has been submitted to moderation.")
        st.rerun()

# B. INPUTS FOR OTHER STEPS
else:
    # 1. Selection Grids (Genre, Explicit, etc)
    if step == "S1_GENRE":
        genres = ["Pop", "Hip Hop", "Rock", "R&B", "Electronic", "Children's Music", "Other"]
        cols = st.columns(4)
        for i, g in enumerate(genres):
            if cols[i%4].button(g):
                process_input(g)
                st.rerun()

    elif step == "S2_LYRICS_TYPE":
        c1, c2, c3 = st.columns(3)
        if c1.button("Instrumental"):
            data["lyrics_type"] = "Instrumental"
            data["lyricists"] = [] # Clear lyricists
            add_msg("user", "Instrumental")
            add_msg("assistant", "Instrumental track. Skipping lyricist fields. **Explicit Content?**")
            st.session_state.step = "S2_EXPLICIT"
            st.rerun()
        if c2.button("English"):
            data["lyrics_type"] = "English"
            add_msg("user", "English")
            add_msg("assistant", "Got it. Who are the **Lyricists**? (Legal Name).")
            st.session_state.step = "S2_LYRICISTS"
            st.rerun()

    elif step == "S2_EXPLICIT":
        c1, c2, c3 = st.columns(3)
        if c1.button("Clean"): 
            data["explicit"] = "Clean"
            add_msg("user", "Clean")
            add_msg("assistant", "Marked Clean. **ISRC**? (Optional)")
            st.session_state.step = "S2_ISRC"
            st.rerun()
        if c2.button("Explicit"):
             data["explicit"] = "Explicit"
             add_msg("user", "Explicit")
             add_msg("assistant", "Marked Explicit. **ISRC**? (Optional)")
             st.session_state.step = "S2_ISRC"
             st.rerun()

    # 2. Loop Handlers (Composers)
    elif step == "S2_COMPOSERS":
        with st.form("comp_form"):
            val = st.text_input("Composer Name")
            c1, c2 = st.columns(2)
            if c1.form_submit_button("Add Composer"):
                process_input(val)
                st.rerun()
            if c2.form_submit_button("Next Step ➝"):
                add_msg("user", "Next")
                add_msg("assistant", "Moving to **Performers**.")
                st.session_state.step = "S2_PERFORMERS"
                st.rerun()

    # 3. File Uploaders
    elif step == "S2_AUDIO":
        f = st.file_uploader("Upload WAV/MP3", type=["wav", "mp3"])
        if f: 
            data["audio_file"] = f
            add_msg("user", "📁 Audio Uploaded")
            process_input("Audio")
            st.rerun()
            
    elif step == "S3_COVER":
        f = st.file_uploader("Upload JPG/PNG (3000px)", type=["jpg", "png"])
        if f:
            data["cover_art"] = f
            add_msg("user", "📁 Art Uploaded")
            process_input("Art")
            st.rerun()

    # 4. Standard Text Input
    else:
        v = st.chat_input("Type your answer here...")
        if v:
            process_input(v)
            st.rerun()
