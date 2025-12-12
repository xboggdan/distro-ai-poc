import streamlit as st
import time
import uuid

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="BandLab DistroBot", page_icon="🔥", layout="wide")

st.markdown("""
<style>
    /* BANDLAB BRANDING */
    .stApp { background-color: #ffffff; color: #222; }
    
    /* Chat Bubbles */
    .stChatMessage {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 15px;
    }
    
    /* Primary Button (Red) */
    .stButton > button {
        background-color: #F50000;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 8px 24px;
        font-weight: 600;
    }
    .stButton > button:hover { background-color: #d10000; color: white; }

    /* Secondary Button (Gray/Ghost) */
    div[data-testid="column"] > div > div > div > button.secondary {
        background-color: transparent;
        color: #333;
        border: 1px solid #ccc;
    }

    /* Review Card */
    .review-card {
        border: 1px solid #eee;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .review-row {
        display: flex; justify-content: space-between;
        padding: 8px 0; border-bottom: 1px solid #f0f0f0;
    }
    .review-label { color: #666; font-size: 0.9em; }
    .review-val { font-weight: 600; }
    
    /* Education Box */
    .edu-box {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 15px; margin-bottom: 15px; font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA LISTS (FROM SCREENSHOTS) ---
GENRES = ["Pop", "Hip Hop", "Rock", "R&B", "Electronic", "Children's Music", "Country", "Alternative"]
INSTRUMENTS = ["Vocals", "Guitar", "Bass", "Drums", "Keys", "Banjo", "Violin", "Synth", "Other"]
PROD_ROLES = ["Producer", "Recording Engineer", "Mixing Engineer", "Mastering Engineer", "Assistant Engineer"]
LANGUAGES = ["English", "Spanish", "French", "German", "Instrumental"]

# --- 3. STATE MANAGEMENT ---

def init_state():
    defaults = {
        "history": [{
            "role": "assistant", 
            "content": "🔥 **Let's Build Your Release.**\n\nI'll guide you step-by-step. I've detected your Main Artist profile is **xboggdan**.\n\n**Step 1:** What is the **Release Title**?"
        }],
        "step": "S1_TITLE", 
        "edu_mode": False,
        "edit_return_mode": False, # If True, jumps back to Review after 1 input
        
        # TEMP HOLDERS FOR COMPLEX INPUTS
        "temp_name": "", 
        "temp_role": "",
        
        # THE DATA PAYLOAD
        "data": {
            "main_artist": "xboggdan",
            "release_title": "",
            "version": "",
            "genre": "",
            "upc": "",
            "release_date": "ASAP",
            "label": "",
            
            # Complex Arrays
            "composers": [], # List of names
            "performers": [], # List of {name, instrument}
            "production": [], # List of {name, role}
            "lyricists": [], # List of names
            
            "lyrics_lang": "English",
            "explicit": "Clean",
            "isrc": "",
            "publisher": "",
            "audio": None,
            "cover": None
        }
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# --- 4. EDUCATION CONTENT ---
KB = {
    "UPC": "Universal Product Code. Identifies the album/single product.",
    "Composers": "Requires **Legal First & Last Name** (e.g., 'John Smith', not 'J-Dawg') for royalty collection.",
    "Performers": "Anyone who played an instrument or sang on the track.",
    "Lyricists": "Required for any song that isn't Instrumental.",
    "Explicit": "Must be marked if the song contains profanity or references to violence/drugs.",
    "ISRC": "International Standard Recording Code. Identifies the specific audio recording."
}

# --- 5. LOGIC HANDLERS (CALLBACKS) ---

def add_msg(role, text):
    st.session_state.history.append({"role": role, "content": text})

def next_step(step_id, bot_msg):
    # If we were editing, go back to review
    if st.session_state.edit_return_mode:
        st.session_state.edit_return_mode = False
        st.session_state.step = "REVIEW"
        add_msg("assistant", "✅ Updated. Returning to Review.")
    else:
        st.session_state.step = step_id
        add_msg("assistant", bot_msg)

# --- INPUT PROCESSING FUNCTIONS ---

def handle_text(key_name, next_s, prompt):
    val = st.session_state.user_input
    if val:
        st.session_state.data[key_name] = val
        add_msg("user", val)
        next_step(next_s, prompt)

def handle_btn(val, key_name, next_s, prompt):
    if key_name: st.session_state.data[key_name] = val
    add_msg("user", str(val))
    next_step(next_s, prompt)

# --- COMPLEX LOGIC HANDLERS (The "Smart" Parts) ---

def add_composer_smart(is_me):
    d = st.session_state.data
    if is_me:
        # User clicked "Yes, it's me"
        # In real app, we'd pull legal name from profile. Here we simulate or ask.
        add_msg("user", "Yes, I am the composer")
        add_msg("assistant", f"Using your profile name (**{d['main_artist']}**). Any other composers?")
        d['composers'].append(d['main_artist'])
        st.session_state.step = "S2_COMPOSERS_MORE"
    else:
        add_msg("user", "No / Add Another")
        add_msg("assistant", "Please enter the **Legal First & Last Name** of the composer.")
        st.session_state.step = "S2_COMPOSERS_INPUT"

def save_composer_input():
    val = st.session_state.user_input
    if len(val.split()) < 2:
        st.toast("⚠️ Legal Name requires First & Last Name")
        return
    st.session_state.data['composers'].append(val)
    add_msg("user", val)
    next_step("S2_COMPOSERS_MORE", f"Added {val}. Any others?")

def add_performer_smart(is_me):
    if is_me:
        add_msg("user", "Yes, I performed")
        st.session_state.temp_name = st.session_state.data['main_artist']
        next_step("S2_PERF_ROLE", f"What instrument did **{st.session_state.temp_name}** play?")
    else:
        add_msg("user", "Add Another Person")
        next_step("S2_PERF_NAME", "Enter the Performer's Name:")

def save_performer_role(role):
    name = st.session_state.temp_name
    st.session_state.data['performers'].append({"name": name, "role": role})
    add_msg("user", role)
    next_step("S2_PERF_MORE", f"Added {name} on {role}. Anyone else?")

# --- 6. UI RENDERERS ---

def render_sidebar():
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/BandLab_Technologies_logo.svg/2560px-BandLab_Technologies_logo.svg.png", width=150)
        st.markdown("### 🛠 Options")
        st.session_state.edu_mode = st.toggle("🎓 Education Mode", value=st.session_state.edu_mode)
        
        if st.session_state.edu_mode:
            st.info("Information about specific fields will appear in the chat.")

        # Progress
        d = st.session_state.data
        if d['cover']:
            st.image(d['cover'], caption="Cover Art", width=200)
        elif d['release_title']:
            st.markdown(f"**Draft:** {d['release_title']}")

        if st.button("Start Over"):
            st.session_state.clear()
            st.rerun()

def render_history():
    for msg in st.session_state.history:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])

def inject_edu(step_keyword):
    if st.session_state.edu_mode and step_keyword in KB:
        st.markdown(f"<div class='edu-box'>🎓 <b>Info:</b> {KB[step_keyword]}</div>", unsafe_allow_html=True)

# --- 7. MAIN INPUT ROUTER ---

def render_inputs():
    step = st.session_state.step
    d = st.session_state.data

    # --- STEP 1: RELEASE INFO ---
    if step == "S1_TITLE":
        st.chat_input("Enter Title...", key="user_input", on_submit=lambda: handle_text("release_title", "S1_VERSION", "Any specific Version? (Type 'None' to skip)"))

    elif step == "S1_VERSION":
        st.chat_input("e.g. Deluxe, Remastered...", key="user_input", on_submit=lambda: handle_text("version", "S1_GENRE", "Select the Genre."))

    elif step == "S1_GENRE":
        cols = st.columns(4)
        for i, g in enumerate(GENRES):
            if cols[i%4].button(g, use_container_width=True):
                handle_btn(g, "genre", "S1_DATE", "When is the release date?")

    elif step == "S1_DATE":
        c1, c2 = st.columns(2)
        if c1.button("As Soon As Possible", use_container_width=True):
            handle_btn("ASAP", "release_date", "S1_UPC", "Do you have a UPC? (Type 'None' to generate free)")
        if c2.button("Specific Date", use_container_width=True):
             # Simplified for demo
            handle_btn("Specific", "release_date", "S1_UPC", "Do you have a UPC? (Type 'None' to generate free)")

    elif step == "S1_UPC":
        inject_edu("UPC")
        st.chat_input("12-13 digits or 'None'...", key="user_input", on_submit=lambda: handle_text("upc", "S1_LABEL", "Label Name? (Type 'None' for Independent)"))

    elif step == "S1_LABEL":
        st.chat_input("Label Name...", key="user_input", on_submit=lambda: handle_text("label", "S2_COMPOSERS_START", "Moving to Track Details.\n\n**Composers:** Is **xboggdan** the composer?"))

    # --- STEP 2: TRACK & ROLES (SMART LOGIC) ---
    
    # 1. COMPOSERS
    elif step == "S2_COMPOSERS_START":
        inject_edu("Composers")
        c1, c2 = st.columns(2)
        if c1.button(f"Yes, {d['main_artist']} composed it", use_container_width=True):
            add_composer_smart(True)
            st.rerun()
        if c2.button("No / Someone Else", use_container_width=True):
            add_composer_smart(False)
            st.rerun()

    elif step == "S2_COMPOSERS_INPUT":
        inject_edu("Composers")
        st.chat_input("Legal First & Last Name...", key="user_input", on_submit=save_composer_input)

    elif step == "S2_COMPOSERS_MORE":
        c1, c2 = st.columns(2)
        if c1.button("Add Another Composer", use_container_width=True):
            next_step("S2_COMPOSERS_INPUT", "Enter the next name.")
            st.rerun()
        if c2.button("Done with Composers", use_container_width=True):
            next_step("S2_PERF_START", f"**Performers:** Did **{d['main_artist']}** perform on this track?")
            st.rerun()

    # 2. PERFORMERS
    elif step == "S2_PERF_START":
        inject_edu("Performers")
        c1, c2 = st.columns(2)
        if c1.button(f"Yes, {d['main_artist']} performed", use_container_width=True):
            add_performer_smart(True)
            st.rerun()
        if c2.button("No / Add Others", use_container_width=True):
            add_performer_smart(False)
            st.rerun()

    elif step == "S2_PERF_NAME":
        st.chat_input("Performer Name...", key="user_input", on_submit=lambda: 
                      (setattr(st.session_state, 'temp_name', st.session_state.user_input), 
                       add_msg("user", st.session_state.user_input),
                       next_step("S2_PERF_ROLE", f"What instrument did **{st.session_state.user_input}** play?")))

    elif step == "S2_PERF_ROLE":
        cols = st.columns(4)
        for i, inst in enumerate(INSTRUMENTS):
            if cols[i%4].button(inst, use_container_width=True):
                save_performer_role(inst)
                st.rerun()

    elif step == "S2_PERF_MORE":
        c1, c2 = st.columns(2)
        if c1.button("Add Another Performer", use_container_width=True):
            next_step("S2_PERF_NAME", "Enter Name:")
            st.rerun()
        if c2.button("Done with Performers", use_container_width=True):
            next_step("S2_PROD_START", "**Production:** Add producers or engineers?")
            st.rerun()

    # 3. PRODUCTION (Simplified for demo, similar flow to Perf)
    elif step == "S2_PROD_START":
        c1, c2 = st.columns(2)
        if c1.button("Add Producer/Engineer", use_container_width=True):
             next_step("S2_PROD_NAME", "Enter Name:")
             st.rerun()
        if c2.button("Skip / Done", use_container_width=True):
             next_step("S2_LYRICS_LANG", "**Lyrics:** What is the language?")
             st.rerun()
             
    elif step == "S2_PROD_NAME":
        st.chat_input("Name...", key="user_input", on_submit=lambda: 
                      (setattr(st.session_state, 'temp_name', st.session_state.user_input),
                       next_step("S2_PROD_ROLE", "Select Role:")))
                       
    elif step == "S2_PROD_ROLE":
        for role in PROD_ROLES:
            if st.button(role, use_container_width=True):
                d['production'].append({"name": st.session_state.temp_name, "role": role})
                next_step("S2_PROD_START", f"Added {st.session_state.temp_name} ({role}). Add another?")
                st.rerun()

    # 4. LYRICS & EXPLICIT
    elif step == "S2_LYRICS_LANG":
        for lang in LANGUAGES:
            if st.button(lang, use_container_width=True):
                d['lyrics_lang'] = lang
                if lang == "Instrumental":
                    handle_btn(lang, "lyrics_lang", "S2_EXPLICIT", "Instrumental set. Is the content **Explicit**?")
                else:
                    handle_btn(lang, "lyrics_lang", "S2_LYRICIST", f"{lang} selected. Who is the **Lyricist**?")
                st.rerun()

    elif step == "S2_LYRICIST":
        inject_edu("Lyricists")
        c1, c2 = st.columns(2)
        if c1.button(f"{d['main_artist']}", use_container_width=True):
            d['lyricists'].append(d['main_artist'])
            next_step("S2_EXPLICIT", "Lyricist added. Is the track **Explicit**?")
            st.rerun()
        if c2.button("Someone Else", use_container_width=True):
            st.session_state.step = "S2_LYRICIST_INPUT"
            st.rerun()
            
    elif step == "S2_LYRICIST_INPUT":
        st.chat_input("Legal Name...", key="user_input", on_submit=lambda: 
                      (d['lyricists'].append(st.session_state.user_input),
                       next_step("S2_EXPLICIT", "Lyricist added. Is the track **Explicit**?")))

    elif step == "S2_EXPLICIT":
        inject_edu("Explicit")
        c1, c2 = st.columns(2)
        if c1.button("Clean / Non-Explicit", use_container_width=True):
            handle_btn("Clean", "explicit", "S2_ISRC", "Marked Clean. **ISRC**? (Optional)")
        if c2.button("Explicit (Parental Advisory)", use_container_width=True):
            handle_btn("Explicit", "explicit", "S2_ISRC", "Marked Explicit. **ISRC**? (Optional)")

    elif step == "S2_ISRC":
        inject_edu("ISRC")
        st.chat_input("Enter ISRC or 'None'...", key="user_input", on_submit=lambda: handle_text("isrc", "S2_AUDIO", "Upload your **Audio File**."))

    # --- STEP 3: ASSETS ---
    elif step == "S2_AUDIO":
        f = st.file_uploader("WAV / MP3 / M4A", type=["wav", "mp3", "m4a", "ogg"])
        if f:
            d['audio'] = f
            add_msg("user", "📁 Audio Uploaded")
            next_step("S3_COVER", "Great. Finally, upload your **Cover Art**.")
            st.rerun()

    elif step == "S3_COVER":
        f = st.file_uploader("JPG / PNG (3000x3000px)", type=["jpg", "png"])
        if f:
            d['cover'] = f
            add_msg("user", "🖼️ Art Uploaded")
            next_step("REVIEW", "🎉 All data collected! Please review your release below.")
            st.rerun()

    # --- STEP 4: REVIEW & EDIT ---
    elif step == "REVIEW":
        st.markdown("---")
        st.subheader("💿 Release Summary")
        
        # Helper for Edit Rows
        def row(label, val, edit_step):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{label}:** {val}")
            with c2:
                if st.button("Edit", key=f"edit_{label}"):
                    st.session_state.edit_return_mode = True
                    st.session_state.step = edit_step
                    add_msg("assistant", f"Ok, enter the new **{label}**:")
                    st.rerun()

        row("Title", d['release_title'], "S1_TITLE")
        row("Genre", d['genre'], "S1_GENRE")
        row("UPC", d['upc'], "S1_UPC")
        
        st.divider()
        st.markdown("**Credits**")
        st.write(f"**Composers:** {', '.join(d['composers'])}")
        
        for p in d['performers']:
            st.write(f"**{p['name']}**: {p['role']}")
            
        st.divider()
        row("Explicit", d['explicit'], "S2_EXPLICIT")
        row("ISRC", d['isrc'], "S2_ISRC")
        
        st.markdown("---")
        if st.button("🚀 SUBMIT TO STORES", use_container_width=True):
            st.balloons()
            st.success("Submitted successfully!")

# --- 8. APP EXECUTION ---

render_sidebar()
st.title("BandLab Distribution")
render_history()
st.markdown("---")
render_inputs()
