import streamlit as st
import time

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
        transition: 0.2s;
    }
    .stButton > button:hover { background-color: #d10000; color: white; }

    /* Education Box (Fixed Visibility) */
    .edu-box {
        background-color: #FFF8E1;
        border: 1px solid #FFE082;
        border-left: 5px solid #FFC107;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        color: #5D4037;
        font-size: 0.95em;
    }
    .edu-title { font-weight: bold; color: #F57F17; display: block; margin-bottom: 5px;}
    
    /* Tutorial Card */
    .tutorial-card {
        border: 1px solid #eee;
        padding: 25px;
        border-radius: 12px;
        background: #fafafa;
        text-align: center;
        margin-bottom: 20px;
    }
    .feature-grid { display: flex; gap: 10px; justify-content: center; margin-top: 20px; }
    .feature-item { background: white; padding: 15px; border-radius: 8px; border: 1px solid #eee; width: 30%; font-size: 0.8em; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA & STATE ---

GENRES = ["Pop", "Hip Hop", "Rock", "R&B", "Electronic", "Children's Music", "Country", "Alternative"]
INSTRUMENTS = ["Vocals", "Guitar", "Bass", "Drums", "Keys", "Banjo", "Violin", "Synth", "Other"]
PROD_ROLES = ["Producer", "Recording Engineer", "Mixing Engineer", "Mastering Engineer"]
LANGUAGES = ["English", "Spanish", "French", "German", "Instrumental"]

# KNOWLEDGE BASE (Mapped directly to Step IDs)
KB = {
    "S1_UPC": {
        "title": "What is a UPC?",
        "text": "The **Universal Product Code** is the barcode for your release. It identifies the product (album/single) for sales tracking. If you don't have one, we generate it for free."
    },
    "S1_LABEL": {
        "title": "Record Label",
        "text": "This is the name that appears under the release date on Spotify. Independent artists often use their own artist name or a custom brand name here."
    },
    "S2_COMPOSERS_START": {
        "title": "Why do we need Composers?",
        "text": "Streaming services pay **Publishing Royalties** separate from artist royalties. To collect this money, we need the **Legal First & Last Name** of every songwriter."
    },
    "S2_COMPOSERS_INPUT": {
        "title": "Legal Names Only",
        "text": "Do not use stage names (e.g. 'Jay-Z') here. Use the name on their government ID (e.g. 'Shawn Carter') to ensure royalty attribution."
    },
    "S2_EXPLICIT": {
        "title": "Explicit Content Rules",
        "text": "You must flag 'Explicit' if lyrics contain: strong language, references to violence, discriminatory language, or drug use. Failure to do so can result in takedowns."
    },
    "S2_ISRC": {
        "title": "What is an ISRC?",
        "text": "The **International Standard Recording Code** is the unique fingerprint for this specific audio recording. It tracks streams across different albums (e.g. if this song is on a Greatest Hits later)."
    },
    "S3_COVER": {
        "title": "Cover Art Guidelines",
        "text": "Strict Rules: 3000x3000px, JPG/PNG. **No** URLs, **No** social media handles, **No** pricing, **No** blurry images, and **No** copyrighted brands."
    }
}

def init_state():
    if "history" not in st.session_state:
        st.session_state.update({
            "history": [], # Start empty, tutorial screen first
            "step": "INTRO", 
            "edu_mode": False,
            "edit_return_mode": False,
            "temp_name": "",
            "data": {
                "main_artist": "xboggdan",
                "release_title": "", "version": "", "genre": "", "upc": "", "release_date": "ASAP", "label": "",
                "composers": [], "performers": [], "production": [], "lyricists": [],
                "lyrics_lang": "English", "explicit": "Clean", "isrc": "", "audio": None, "cover": None
            }
        })

init_state()

# --- 3. LOGIC HANDLERS ---

def add_msg(role, text):
    st.session_state.history.append({"role": role, "content": text})

def next_step(step_id, bot_msg):
    if st.session_state.edit_return_mode:
        st.session_state.edit_return_mode = False
        st.session_state.step = "REVIEW"
        add_msg("assistant", "✅ Updated. Returning to Review.")
    else:
        st.session_state.step = step_id
        add_msg("assistant", bot_msg)

def start_chat():
    st.session_state.step = "S1_TITLE"
    add_msg("assistant", "🔥 **Let's get started.**\n\nI'll guide you step-by-step. I've detected your Main Artist profile is **xboggdan**.\n\n**Step 1:** What is the **Release Title**?")

# --- SMART ADDERS ---
def add_composer_smart(is_me):
    d = st.session_state.data
    if is_me:
        add_msg("user", "Yes, I am the composer")
        d['composers'].append(d['main_artist'])
        next_step("S2_COMPOSERS_MORE", f"Added **{d['main_artist']}**. Any other composers?")
    else:
        add_msg("user", "Someone Else")
        next_step("S2_COMPOSERS_INPUT", "Enter the **Legal First & Last Name**:")

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

# --- 4. UI RENDERERS ---

def render_sidebar():
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/BandLab_Technologies_logo.svg/2560px-BandLab_Technologies_logo.svg.png", width=150)
        st.markdown("### 🛠 Options")
        
        # TOGGLE
        st.session_state.edu_mode = st.toggle("🎓 Education Mode", value=st.session_state.edu_mode)
        if st.session_state.edu_mode:
            st.caption("I will explain technical terms as we go.")

        st.divider()
        st.markdown("### 📀 Live Draft")
        d = st.session_state.data
        if d['release_title']:
            st.markdown(f"**{d['release_title']}**")
            st.caption(f"{d['main_artist']}")
        else:
            st.caption("No data yet.")
        
        if st.button("Restart Session"):
            st.session_state.clear()
            st.rerun()

def render_tutorial():
    st.markdown("""
    <div class="tutorial-card">
        <h2>🔥 Welcome to DistroBot</h2>
        <p>The smartest way to release your music to Spotify, Apple Music, and beyond.</p>
        <hr style="opacity:0.2;">
        <div style="text-align:left; margin-bottom:20px;">
            <p><b>🤔 What is this tool?</b><br>
            This is an AI-powered A&R agent. Instead of filling out boring forms, you chat with it. It validates your metadata, checks your artwork for illegal text, and ensures your release meets DSP standards so you don't get rejected.</p>
            <p><b>🚀 Key Features:</b></p>
            <ul>
                <li><b>Smart Auto-Fill:</b> Detects your profile to skip typing.</li>
                <li><b>Guardrails:</b> Prevents common mistakes (like putting "feat." in titles).</li>
                <li><b>Education Mode:</b> Teaches you about royalties and metadata as you type.</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🚀 Start My Release", use_container_width=True):
            start_chat()
            st.rerun()

def render_edu_box():
    # Looks up the CURRENT step in the KB dictionary
    step = st.session_state.step
    if st.session_state.edu_mode and step in KB:
        info = KB[step]
        st.markdown(f"""
        <div class="edu-box">
            <span class="edu-title">🎓 {info['title']}</span>
            {info['text']}
        </div>
        """, unsafe_allow_html=True)

# --- 5. MAIN APP FLOW ---

render_sidebar()

if st.session_state.step == "INTRO":
    render_tutorial()

else:
    st.title("BandLab Distribution")
    
    # 1. Chat History
    for msg in st.session_state.history:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])
            
    # 2. Education Injection (Appears RIGHT above input)
    render_edu_box()
    
    # 3. Dynamic Inputs
    step = st.session_state.step
    d = st.session_state.data
    
    # --- TEXT INPUT HANDLERS ---
    if step == "S1_TITLE":
        st.chat_input("Enter Release Title...", key="user_input", on_submit=lambda: (st.session_state.data.update({"release_title": st.session_state.user_input}), add_msg("user", st.session_state.user_input), next_step("S1_VERSION", "Any specific Version? (Type 'None' to skip)")))
    
    elif step == "S1_VERSION":
        st.chat_input("e.g. Radio Edit...", key="user_input", on_submit=lambda: (st.session_state.data.update({"version": st.session_state.user_input}), add_msg("user", st.session_state.user_input), next_step("S1_GENRE", "Select Genre:")))
        
    elif step == "S1_UPC":
        st.chat_input("Enter UPC or 'None'...", key="user_input", on_submit=lambda: (st.session_state.data.update({"upc": st.session_state.user_input}), add_msg("user", st.session_state.user_input), next_step("S1_LABEL", "Record Label Name?")))

    elif step == "S1_LABEL":
        st.chat_input("Label Name...", key="user_input", on_submit=lambda: (st.session_state.data.update({"label": st.session_state.user_input}), add_msg("user", st.session_state.user_input), next_step("S2_COMPOSERS_START", f"**Composers:** Is **{d['main_artist']}** the composer?")))

    elif step == "S2_COMPOSERS_INPUT":
        st.chat_input("Legal First & Last Name...", key="user_input", on_submit=save_composer_input)

    elif step == "S2_PERF_NAME":
        st.chat_input("Performer Name...", key="user_input", on_submit=lambda: (setattr(st.session_state, 'temp_name', st.session_state.user_input), add_msg("user", st.session_state.user_input), next_step("S2_PERF_ROLE", f"Instrument for **{st.session_state.user_input}**?")))
    
    elif step == "S2_PROD_NAME":
        st.chat_input("Producer Name...", key="user_input", on_submit=lambda: (setattr(st.session_state, 'temp_name', st.session_state.user_input), next_step("S2_PROD_ROLE", "Select Role:")))

    elif step == "S2_LYRICIST_INPUT":
        st.chat_input("Lyricist Legal Name...", key="user_input", on_submit=lambda: (d['lyricists'].append(st.session_state.user_input), next_step("S2_EXPLICIT", "Is the track **Explicit**?")))

    elif step == "S2_ISRC":
        st.chat_input("ISRC or 'None'...", key="user_input", on_submit=lambda: (st.session_state.data.update({"isrc": st.session_state.user_input}), add_msg("user", st.session_state.user_input), next_step("S2_AUDIO", "Upload **Audio File**.")))

    # --- BUTTON/GRID HANDLERS ---
    
    elif step == "S1_GENRE":
        cols = st.columns(4)
        for i, g in enumerate(GENRES):
            if cols[i%4].button(g, use_container_width=True):
                st.session_state.data["genre"] = g
                add_msg("user", g)
                next_step("S1_DATE", "Release Date?")

    elif step == "S1_DATE":
        c1, c2 = st.columns(2)
        if c1.button("ASAP", use_container_width=True):
            st.session_state.data["release_date"] = "ASAP"
            add_msg("user", "ASAP")
            next_step("S1_UPC", "Do you have a UPC?")
        if c2.button("Pick Date", use_container_width=True):
            next_step("S1_UPC", "Do you have a UPC?") # Skipping calendar for demo

    elif step == "S2_COMPOSERS_START":
        c1, c2 = st.columns(2)
        if c1.button(f"Yes, {d['main_artist']}", use_container_width=True):
            add_composer_smart(True)
            st.rerun()
        if c2.button("No / Someone Else", use_container_width=True):
            add_composer_smart(False)
            st.rerun()
            
    elif step == "S2_COMPOSERS_MORE":
        c1, c2 = st.columns(2)
        if c1.button("Add Another Composer", use_container_width=True):
            next_step("S2_COMPOSERS_INPUT", "Enter Name:")
            st.rerun()
        if c2.button("Done", use_container_width=True):
            next_step("S2_PERF_START", f"**Performers:** Did **{d['main_artist']}** perform?")
            st.rerun()

    elif step == "S2_PERF_START":
        c1, c2 = st.columns(2)
        if c1.button(f"Yes, {d['main_artist']}", use_container_width=True):
            add_performer_smart(True)
            st.rerun()
        if c2.button("No / Someone Else", use_container_width=True):
            add_performer_smart(False)
            st.rerun()

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
        if c2.button("Done", use_container_width=True):
            next_step("S2_PROD_START", "**Production:** Add producers?")
            st.rerun()

    elif step == "S2_PROD_START":
        c1, c2 = st.columns(2)
        if c1.button("Add Producer", use_container_width=True):
            next_step("S2_PROD_NAME", "Enter Name:")
            st.rerun()
        if c2.button("Skip / Done", use_container_width=True):
            next_step("S2_LYRICS_LANG", "Language?")
            st.rerun()

    elif step == "S2_PROD_ROLE":
        for role in PROD_ROLES:
            if st.button(role, use_container_width=True):
                d['production'].append({"name": st.session_state.temp_name, "role": role})
                next_step("S2_PROD_START", "Added. Add another?")
                st.rerun()
                
    elif step == "S2_LYRICS_LANG":
        for lang in LANGUAGES:
            if st.button(lang, use_container_width=True):
                d['lyrics_lang'] = lang
                if lang == "Instrumental":
                    add_msg("user", lang)
                    next_step("S2_EXPLICIT", "Instrumental set. Is it **Explicit**?")
                else:
                    add_msg("user", lang)
                    next_step("S2_LYRICIST", "Who is the **Lyricist**?")
                st.rerun()

    elif step == "S2_LYRICIST":
        c1, c2 = st.columns(2)
        if c1.button(f"{d['main_artist']}", use_container_width=True):
            d['lyricists'].append(d['main_artist'])
            next_step("S2_EXPLICIT", "Explicit Content?")
            st.rerun()
        if c2.button("Someone Else", use_container_width=True):
            next_step("S2_LYRICIST_INPUT", "Enter Legal Name:")
            st.rerun()

    elif step == "S2_EXPLICIT":
        c1, c2 = st.columns(2)
        if c1.button("Clean", use_container_width=True):
            st.session_state.data["explicit"] = "Clean"
            add_msg("user", "Clean")
            next_step("S2_ISRC", "Do you have an ISRC?")
        if c2.button("Explicit", use_container_width=True):
            st.session_state.data["explicit"] = "Explicit"
            add_msg("user", "Explicit")
            next_step("S2_ISRC", "Do you have an ISRC?")

    # --- FILES ---
    elif step == "S2_AUDIO":
        f = st.file_uploader("Upload Audio", type=["wav","mp3"])
        if f:
            d['audio'] = f
            add_msg("user", "Audio Uploaded")
            next_step("S3_COVER", "Upload **Cover Art**.")
            st.rerun()
            
    elif step == "S3_COVER":
        f = st.file_uploader("Upload Cover", type=["jpg","png"])
        if f:
            d['cover'] = f
            add_msg("user", "Art Uploaded")
            next_step("REVIEW", "Review your release.")
            st.rerun()

    # --- REVIEW ---
    elif step == "REVIEW":
        st.subheader("💿 Release Summary")
        
        def review_row(label, val, edit_step):
            c1, c2 = st.columns([4,1])
            c1.markdown(f"**{label}:** {val}")
            if c2.button("Edit", key=label):
                st.session_state.edit_return_mode = True
                st.session_state.step = edit_step
                add_msg("assistant", f"Enter new **{label}**:")
                st.rerun()

        review_row("Title", d['release_title'], "S1_TITLE")
        review_row("UPC", d['upc'], "S1_UPC")
        review_row("Explicit", d['explicit'], "S2_EXPLICIT")
        
        st.divider()
        st.write(f"**Composers:** {', '.join(d['composers'])}")
        st.write(f"**Performers:** {len(d['performers'])} added")
        
        if st.button("🚀 SUBMIT", use_container_width=True):
            st.balloons()
            st.success("Release Submitted!")
