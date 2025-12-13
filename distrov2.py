import streamlit as st
import time
import uuid

# --- 1. SETUP & IMPORTS ---
try:
    from groq import Groq
    import google.generativeai as genai
    from openai import OpenAI
except ImportError:
    pass

# --- 2. CONFIGURATION & STYLING ---
st.set_page_config(page_title="BandLab Distribution V14", page_icon="🔥", layout="wide")

st.markdown("""
<style>
    /* GLOBAL THEME */
    .stApp { background-color: #FAFAFA; color: #222; font-family: 'Inter', sans-serif; }
    
    /* THE FOCUS CARD */
    .focus-card {
        background-color: white;
        padding: 40px;
        border-radius: 20px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        margin-bottom: 30px;
        text-align: center;
        max-width: 900px;
        margin-left: auto;
        margin-right: auto;
    }
    
    /* Typography */
    .question-header { font-size: 28px; font-weight: 700; color: #111; margin-bottom: 10px; }
    .question-sub { font-size: 16px; color: #666; margin-bottom: 25px; }
    
    /* AI Tip Box (Education Mode) */
    .edu-container {
        background-color: #FFFBEB; 
        border: 1px solid #FCD34D; 
        color: #92400E;
        padding: 15px; 
        border-radius: 12px; 
        font-size: 0.95em; 
        margin: 20px auto;
        max-width: 700px; 
        text-align: left;
        display: flex;
        align-items: flex-start;
        gap: 12px;
        box-shadow: 0 2px 5px rgba(251, 191, 36, 0.1);
    }
    .edu-icon { font-size: 1.5em; line-height: 1; }
    .edu-content { flex: 1; }
    .edu-badge {
        font-size: 0.7em; font-weight: bold; text-transform: uppercase;
        background: rgba(255,255,255,0.5); padding: 2px 6px; border-radius: 4px;
        margin-left: 8px; opacity: 0.8;
    }

    /* BUTTONS */
    .stButton > button {
        border-radius: 12px; height: 50px; font-weight: 600; font-size: 16px;
        border: 1px solid #E5E7EB; width: 100%; transition: all 0.2s;
    }
    .stButton > button:hover {
        border-color: #F50000; color: #F50000; background: #FFF5F5; transform: translateY(-2px);
    }
    .primary-action > button {
        background-color: #F50000 !important; color: white !important; border: none !important;
    }

    /* HISTORY LOG */
    .history-log {
        max-width: 900px; margin: 0 auto 20px auto; 
        display: flex; flex-direction: column; gap: 10px;
        opacity: 0.6; transition: opacity 0.3s;
    }
    .history-log:hover { opacity: 1; }
    
    .msg-row { display: flex; align-items: center; gap: 10px; font-size: 0.9em; }
    .msg-user { margin-left: auto; background: #FEE2E2; color: #991B1B; padding: 5px 12px; border-radius: 15px; }
    .msg-bot { margin-right: auto; color: #666; font-style: italic; }

</style>
""", unsafe_allow_html=True)

# --- 3. AI ENGINE (WITH FALLBACK) ---

def ask_ai(prompt):
    """
    Returns (Response_Text, Badge_Label)
    """
    sys_prompt = "You are a concise BandLab Distribution expert. Explain this concept in 1 sentence."
    
    # 1. TRY AI API
    if "GROQ_API_KEY" in st.secrets:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            res = client.chat.completions.create(
                messages=[{"role":"system","content":sys_prompt},{"role":"user","content":prompt}],
                model="llama-3.3-70b-versatile"
            )
            return res.choices[0].message.content, "⚡ Llama 3"
        except: pass

    # 2. INTERNAL DATABASE (FALLBACK)
    # This ensures Education Mode ALWAYS works, even offline.
    kb = {
        "Title": "Titles should be the exact name of the song. Do not include 'feat.' or producer tags here.",
        "Version": "Use 'Radio Edit' or 'Remix' to distinguish alternate takes. Leave blank for the original.",
        "Genre": "This determines which playlists you will be pitched to. Choose the closest match.",
        "Date": "We recommend scheduling 2 weeks in advance to allow time for playlist pitching.",
        "UPC": "Universal Product Code: A barcode used to track sales of your product.",
        "Label": "The name that appears in the 'Source' field on Spotify. Independent artists often use their own name.",
        "Composers": "Streaming services require legal First and Last names to pay publishing royalties.",
        "Performers": "List everyone who played an instrument or sang. This helps with credit database accuracy.",
        "Language": "This helps us route your music to the correct regional editors.",
        "Explicit": "You must mark content as Explicit if it contains profanity, violence, or drug references.",
        "Cover Art": "Art must be 3000x3000px. No URLs, pricing, or social media handles allowed.",
        "Audio": "We accept WAV or MP3 (320kbps). High quality audio ensures the best listener experience."
    }
    
    # Simple keyword match if prompt contains key
    for key, val in kb.items():
        if key in prompt:
            return val, "📚 Knowledge Base"
            
    return "This helps ensure your metadata meets DSP standards.", "⚙️ Logic"

def get_edu_context(step_key):
    """Generates the education tip text"""
    if not st.session_state.edu_mode: return None
    
    # Map step keys to questions
    prompts = {
        "Title": "Explain 'Release Title' rules for Spotify.",
        "Version": "What is a 'Version' in music metadata?",
        "Genre": "Why is genre selection important for distribution?",
        "Date": "Why should I schedule a release date in advance?",
        "UPC": "What is a UPC code?",
        "Label": "What is a Record Label name field used for?",
        "Composers": "Why do I need legal names for Composers?",
        "Performers": "Who counts as a Performer on a track?",
        "Language": "Why does Spotify need the lyrics language?",
        "Explicit": "What are the rules for Explicit content?",
        "Cover Art": "What are the requirements for Cover Art?",
        "Audio": "What audio format is best for distribution?"
    }
    
    if step_key in prompts:
        txt, badge = ask_ai(prompts[step_key])
        return txt, badge
    return None, None

# --- 4. STATE MANAGEMENT ---

def init():
    if "step" not in st.session_state:
        st.session_state.update({
            "step": 1,
            "history": [],
            "edu_mode": False,
            "edit_mode": False,
            "temp_name": "",
            "data": {
                "title": "", "version": "", "artist": "xboggdan", "genre": "", 
                "date": "ASAP", "label": "", "upc": "",
                "composers": [], "performers": [], "producers": [],
                "lang": "English", "explicit": "Clean", "isrc": "",
                "cover": None, "audio": None
            }
        })

def next_step(user_val=None, key=None, save_val=None, jump_to=None):
    # Log History
    if user_val:
        st.session_state.history.append({"role": "user", "text": str(user_val)})
    
    # Save Data
    if key:
        if isinstance(save_val, list): # Append mode
            st.session_state.data[key].append(save_val[0])
        else: # Overwrite mode
            st.session_state.data[key] = save_val
            
    # Advance
    if st.session_state.edit_mode:
        st.session_state.edit_mode = False
        st.session_state.step = 99 # Review
    elif jump_to:
        st.session_state.step = jump_to
    else:
        st.session_state.step += 1
    st.rerun()

# --- 5. UI COMPONENTS ---

def render_history():
    if not st.session_state.history: return
    st.markdown("<div class='history-log'>", unsafe_allow_html=True)
    # Show last 3 items to keep context but keep it clean
    for msg in st.session_state.history[-3:]:
        if msg['role'] == "user":
            st.markdown(f"<div class='msg-row'><div class='msg-user'>{msg['text']}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def render_focus_card(title, subtitle=None, context_key=None):
    # 1. Calculate Education Tip
    tip_html = ""
    if st.session_state.edu_mode and context_key:
        txt, badge = get_edu_context(context_key)
        if txt:
            tip_html = f"""
            <div class="edu-container">
                <div class="edu-icon">🎓</div>
                <div class="edu-content">
                    <b>Did you know?</b><br>{txt}
                    <span class="edu-badge">{badge}</span>
                </div>
            </div>
            """

    # 2. Render Card
    st.markdown(f"""
    <div class="focus-card">
        <div class="question-header">{title}</div>
        {f'<div class="question-sub">{subtitle}</div>' if subtitle else ''}
        {tip_html}
    """, unsafe_allow_html=True)
    
    # The actual widget will be rendered below this function call, 
    # but inside the div visually due to layout
    st.markdown("</div>", unsafe_allow_html=True)

# --- 6. LOGIC FLOW ---

init()
d = st.session_state.data
step = st.session_state.step

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/BandLab_Technologies_logo.svg/2560px-BandLab_Technologies_logo.svg.png", width=140)
    
    # Toggle with instant callback
    st.markdown("### 🎓 Learning Mode")
    mode = st.toggle("Enable AI Tips", value=st.session_state.edu_mode)
    if mode != st.session_state.edu_mode:
        st.session_state.edu_mode = mode
        st.rerun()
        
    st.divider()
    st.markdown("### 💿 Draft")
    if d['title']: st.write(f"**{d['title']}**")
    if d['genre']: st.caption(f"{d['genre']}")
    
    if st.button("Reset"): st.session_state.clear(); st.rerun()

# --- MAIN AREA ---

render_history()

# === STEP 1: TITLE ===
if step == 1:
    render_focus_card("What is the name of your song?", "This will be the main title on Spotify.", "Title")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        val = st.text_input("Title", placeholder="e.g. Midnight City", label_visibility="collapsed")
        if st.button("Next ➝", type="primary"): 
            if val: next_step(val, "title", val)

# === STEP 2: VERSION ===
elif step == 2:
    render_focus_card("Is this a special version?", "Like 'Radio Edit', 'Remix', or 'Live'.", "Version")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("No, Original Mix"): next_step("Original", "version", "")
        st.markdown("<div style='text-align:center;color:#ccc;'>- OR -</div>", unsafe_allow_html=True)
        val = st.text_input("Version", placeholder="e.g. Acoustic", label_visibility="collapsed")
        if val and st.button("Confirm Version"): next_step(val, "version", val)

# === STEP 3: GENRE ===
elif step == 3:
    render_focus_card("Select a primary genre.", context_key="Genre")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        genres = ["Hip Hop", "Pop", "Rock", "R&B", "Electronic", "Country", "Alternative", "Latin"]
        cols = st.columns(2)
        for i, g in enumerate(genres):
            if cols[i%2].button(g, use_container_width=True):
                next_step(g, "genre", g)

# === STEP 4: DATE ===
elif step == 4:
    render_focus_card("When should this go live?", context_key="Date")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("ASAP (As Soon As Possible)"): next_step("ASAP", "date", "ASAP")
        st.markdown("<div style='text-align:center;color:#ccc;'>- OR -</div>", unsafe_allow_html=True)
        dval = st.date_input("Pick Date", label_visibility="collapsed")
        if st.button("Confirm Date"): next_step(str(dval), "date", str(dval))

# === STEP 5: UPC ===
elif step == 5:
    render_focus_card("Do you have a UPC barcode?", "If not, we can generate one for free.", "UPC")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("Generate Free UPC", type="primary"): next_step("Generate Free", "upc", "AUTO")
        val = st.text_input("UPC", placeholder="12-digit UPC", label_visibility="collapsed")
        if val and st.button("Use My UPC"): next_step(val, "upc", val)

# === STEP 6: LABEL ===
elif step == 6:
    render_focus_card("What Record Label is this under?", "Independent artists often use their own name.", "Label")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button(f"Use '{d['artist']}'"): next_step(d['artist'], "label", d['artist'])
        val = st.text_input("Label", placeholder="Label Name", label_visibility="collapsed")
        if val and st.button("Set Label"): next_step(val, "label", val)

# === STEP 7: COMPOSER START ===
elif step == 7:
    render_focus_card("Credits: Who wrote this song?", "Legal names are required for publishing.", "Composers")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown(f"**Is {d['artist']} the songwriter?**")
        if st.button("Yes, It's Me"): 
            st.session_state.data['composers'].append(d['artist'])
            next_step("Yes", jump_to=9)
        if st.button("No / Someone Else"): next_step("Someone Else") # Go to 8

# === STEP 8: COMPOSER MANUAL ===
elif step == 8:
    render_focus_card("Enter Composer's Legal Name", "First and Last name required.", "Composers")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        val = st.text_input("Name", placeholder="e.g. John Smith", label_visibility="collapsed")
        if val and st.button("Add Composer"): 
            st.session_state.data['composers'].append(val)
            next_step(val)

# === STEP 9: COMPOSER LOOP ===
elif step == 9:
    render_focus_card("Composer Added.", "Do you need to add anyone else?", "Composers")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("No, I'm Done", type="primary"): next_step("Done", jump_to=10)
        if st.button("Add Another"): next_step("Add Another", jump_to=8)

# === STEP 10: PERFORMER START ===
elif step == 10:
    render_focus_card("Who performed on this track?", "Vocals, Instruments, etc.", "Performers")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown(f"**Did {d['artist']} perform?**")
        if st.button("Yes"): 
            st.session_state.temp_name = d['artist']
            next_step("Yes", jump_to=11)
        if st.button("No / Someone Else"): next_step("No", jump_to=12)

# === STEP 11: PERFORMER ROLE ===
elif step == 11:
    render_focus_card(f"What did {st.session_state.temp_name} play?", context_key="Performers")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        roles = ["Vocals", "Guitar", "Bass", "Drums", "Keys", "Other"]
        cols = st.columns(2)
        for r in roles:
            if cols[0].button(r, use_container_width=True): 
                st.session_state.data['performers'].append({"name":st.session_state.temp_name, "role":r})
                next_step(r, jump_to=13)

# === STEP 12: PERFORMER MANUAL ===
elif step == 12:
    render_focus_card("Enter Performer Name", context_key="Performers")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        val = st.text_input("Name", label_visibility="collapsed")
        if val and st.button("Next"):
            st.session_state.temp_name = val
            next_step(val, jump_to=11)

# === STEP 13: PERFORMER LOOP ===
elif step == 13:
    render_focus_card("Performer Added.", "Anyone else?", "Performers")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("Done", type="primary"): next_step("Done", jump_to=14)
        if st.button("Add Another"): next_step("Add", jump_to=12)

# === STEP 14: LANGUAGE ===
elif step == 14:
    render_focus_card("Lyrics Language", context_key="Language")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("English"): next_step("English", "lang", "English", jump_to=15)
        if st.button("Instrumental (No Lyrics)"): next_step("Instrumental", "lang", "Instrumental", jump_to=16)

# === STEP 15: EXPLICIT ===
elif step == 15:
    render_focus_card("Explicit Content", "Any profanity or mature themes?", "Explicit")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("Clean / Safe"): next_step("Clean", "explicit", "Clean")
        if st.button("Explicit (Parental Advisory)"): next_step("Explicit", "explicit", "Explicit")

# === STEP 16: FILES ===
elif step == 16:
    render_focus_card("Upload Cover Art", "3000x3000px JPG/PNG", "Cover Art")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        f = st.file_uploader("Cover", type=["jpg","png"], label_visibility="collapsed")
        if f:
            st.session_state.data['cover'] = f
            with st.spinner("🤖 Vision AI checking artwork..."): time.sleep(1.5)
            next_step("Uploaded Art")

elif step == 17:
    render_focus_card("Upload Master Audio", "WAV or MP3", "Audio")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        f = st.file_uploader("Audio", type=["wav","mp3"], label_visibility="collapsed")
        if f:
            st.session_state.data['audio'] = f
            with st.spinner("🎧 Scanning audio copyright..."): time.sleep(1.5)
            next_step("Uploaded Audio", jump_to=99)

# === REVIEW ===
elif step == 99:
    render_focus_card("Release Ready!", "Please review your details below.")
    
    st.markdown("### 📝 Summary")
    st.json(d)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🚀 SUBMIT TO STORES", type="primary"):
            st.balloons()
            st.success("Submitted!")
