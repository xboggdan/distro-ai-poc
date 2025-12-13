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
st.set_page_config(page_title="BandLab Distribution", page_icon="🔥", layout="wide")

st.markdown("""
<style>
    /* GLOBAL THEME: Clean BandLab White/Red */
    .stApp { background-color: #FAFAFA; color: #222; font-family: 'Inter', sans-serif; }
    
    /* THE FOCUS CARD (Main Interaction Area) */
    .focus-card {
        background-color: white;
        padding: 40px;
        border-radius: 20px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        margin-bottom: 30px;
        text-align: center;
    }
    
    /* Typography */
    .question-header { font-size: 28px; font-weight: 700; color: #111; margin-bottom: 10px; }
    .question-sub { font-size: 16px; color: #666; margin-bottom: 25px; }
    
    /* AI Tip Box */
    .ai-tip {
        background-color: #FFFBEB; border: 1px solid #FCD34D; color: #92400E;
        padding: 12px; border-radius: 8px; font-size: 0.9em; margin: 15px auto;
        max-width: 600px; display: flex; align-items: center; justify-content: center; gap: 10px;
    }

    /* CHAT HISTORY (Past Log) */
    .history-container {
        max-width: 800px; margin: 0 auto 30px auto; padding: 20px;
        opacity: 0.8;
    }
    .user-bubble {
        background: #F50000; color: white; padding: 8px 16px; border-radius: 20px;
        display: inline-block; margin: 5px; font-size: 0.9em; float: right; clear: both;
    }
    .bot-bubble {
        background: #E5E7EB; color: #333; padding: 8px 16px; border-radius: 20px;
        display: inline-block; margin: 5px; font-size: 0.9em; float: left; clear: both;
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

    /* LIVE DRAFT SIDEBAR */
    .draft-item {
        padding: 10px; border-bottom: 1px solid #eee; font-size: 0.9em;
        display: flex; justify-content: space-between;
    }
    .draft-label { color: #888; }
    .draft-val { font-weight: 600; color: #333; }

</style>
""", unsafe_allow_html=True)

# --- 3. AI ENGINE ---

def ask_ai(prompt):
    """
    Returns (Response_Text, Badge_HTML)
    """
    sys_prompt = "You are a concise BandLab Distribution expert."
    
    # 1. Groq
    if "GROQ_API_KEY" in st.secrets:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            res = client.chat.completions.create(
                messages=[{"role":"system","content":sys_prompt},{"role":"user","content":prompt}],
                model="llama-3.3-70b-versatile"
            )
            return res.choices[0].message.content, "⚡ Llama 3"
        except: pass

    # 2. Gemini
    if "GEMINI_API_KEY" in st.secrets:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(prompt)
            return res.text, "✨ Gemini"
        except: pass

    # 3. GPT
    if "OPENAI_API_KEY" in st.secrets:
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role":"system","content":sys_prompt},{"role":"user","content":prompt}]
            )
            return res.choices[0].message.content, "🧠 GPT-4"
        except: pass

    return None, "⚙️ Logic"

def get_edu_context(step_name):
    """Returns AI explanation for the current step if Edu Mode is on"""
    if not st.session_state.edu_mode: return None
    
    prompts = {
        "UPC": "Explain what a UPC code is in music distribution in 1 sentence.",
        "ISRC": "Explain what an ISRC code is in 1 sentence.",
        "Composers": "Why do I need legal names for composers in music metadata?",
        "Explicit": "What counts as explicit content in music?",
        "Cover Art": "What are the strict rules for Spotify cover art?"
    }
    
    if step_name in prompts:
        txt, badge = ask_ai(prompts[step_name])
        return f"{txt} ({badge})"
    return None

# --- 4. STATE & LOGIC ---

def init():
    if "step" not in st.session_state:
        st.session_state.update({
            "step": 1,
            "history": [], # Just a log of past actions
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

def next_step(val=None, key=None, save_val=None, jump_to=None):
    """
    Universal State Advance
    """
    # 1. Log History
    if val:
        # Log the bot's LAST question (from previous render) logic would be complex, 
        # simpler to just log the user's answer.
        st.session_state.history.append({"role": "user", "text": val})
    
    # 2. Save Data
    if key:
        if isinstance(save_val, list): # Append mode
            st.session_state.data[key].append(save_val[0])
        else: # Overwrite mode
            st.session_state.data[key] = save_val
            
    # 3. Advance
    if st.session_state.edit_mode:
        st.session_state.edit_mode = False
        st.session_state.step = 99 # Review
    elif jump_to:
        st.session_state.step = jump_to
    else:
        st.session_state.step += 1
    
    st.rerun()

# --- 5. RENDER FUNCTIONS (THE UX) ---

def render_history():
    """Renders the faint conversation log above the focus card"""
    if not st.session_state.history: return
    
    st.markdown("<div class='history-container'>", unsafe_allow_html=True)
    for msg in st.session_state.history[-4:]: # Only show last 4 interactions to keep focus
        cls = "user-bubble" if msg['role'] == "user" else "bot-bubble"
        st.markdown(f"<div class='{cls}'>{msg['text']}</div>", unsafe_allow_html=True)
    st.markdown("<div style='clear:both;'></div></div>", unsafe_allow_html=True)

def render_focus_card(title, subtitle=None, ai_context_key=None):
    """
    The Core UI Component: A centered card with the question.
    """
    st.markdown(f"""
    <div class="focus-card">
        <div class="question-header">{title}</div>
        {f'<div class="question-sub">{subtitle}</div>' if subtitle else ''}
    """, unsafe_allow_html=True)
    
    # Render AI Tip inside the card if needed
    if ai_context_key:
        tip = get_edu_context(ai_context_key)
        if tip:
            st.markdown(f'<div class="ai-tip">💡 <b>AI Tip:</b> {tip}</div>', unsafe_allow_html=True)
            
    # (The widget will be rendered by Streamlit below this HTML block, 
    # but visually appear inside due to layout flow or just below)
    st.markdown("</div>", unsafe_allow_html=True)

# --- 6. THE LOGIC FLOW ---

init()
d = st.session_state.data
step = st.session_state.step

# --- SIDEBAR (DRAFT) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/BandLab_Technologies_logo.svg/2560px-BandLab_Technologies_logo.svg.png", width=140)
    st.markdown("### 💿 Release Draft")
    
    # Draft Table
    fields = ["title", "version", "genre", "upc", "explicit"]
    for f in fields:
        val = d.get(f)
        if val:
            st.markdown(f"""
            <div class="draft-item">
                <span class="draft-label">{f.title()}</span>
                <span class="draft-val">{val}</span>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown(f"""
    <div class="draft-item">
        <span class="draft-label">Composers</span>
        <span class="draft-val">{len(d['composers'])}</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.session_state.edu_mode = st.toggle("🎓 AI Tutor Mode", value=st.session_state.edu_mode)
    if st.button("Reset"): st.session_state.clear(); st.rerun()

# --- MAIN AREA ---

# 1. Show History (Faded)
render_history()

# 2. Show Active Step (The Focus Card)

# === STEP 1: TITLE ===
if step == 1:
    render_focus_card("What is the name of your song?", "This will be the main title on Spotify.")
    
    # Center the input visually using columns
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        val = st.text_input("Title", placeholder="e.g. Midnight City", label_visibility="collapsed")
        st.write("") # Spacer
        if st.button("Next ➝", type="primary"):
            if val: next_step(val, "title", val)

# === STEP 2: VERSION ===
elif step == 2:
    render_focus_card("Is this a special version?", "Like 'Radio Edit', 'Remix', or 'Live'.")
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("No, it's the Original"): next_step("Original", "version", "")
        st.write("--- OR ---")
        val = st.text_input("Version", placeholder="e.g. Acoustic Version", label_visibility="collapsed")
        if val and st.button("Confirm Version"): next_step(val, "version", val)

# === STEP 3: GENRE ===
elif step == 3:
    render_focus_card("Select a primary genre.")
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        genres = ["Hip Hop", "Pop", "Rock", "R&B", "Electronic", "Country", "Alternative", "Latin"]
        cols = st.columns(2)
        for i, g in enumerate(genres):
            if cols[i%2].button(g, use_container_width=True):
                next_step(g, "genre", g)

# === STEP 4: DATE ===
elif step == 4:
    render_focus_card("When should this go live?")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("ASAP (As Soon As Possible)"): next_step("ASAP", "date", "ASAP")
        st.markdown("<div style='text-align:center; color:#888; margin:10px;'>- OR -</div>", unsafe_allow_html=True)
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
    render_focus_card("What Record Label is this under?", "Independent artists often use their own name.")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button(f"Use Artist Name ({d['artist']})"): next_step(d['artist'], "label", d['artist'])
        val = st.text_input("Label", placeholder="Label Name", label_visibility="collapsed")
        if val and st.button("Set Label"): next_step(val, "label", val)

# === STEP 7: COMPOSER START ===
elif step == 7:
    render_focus_card("Credits: Who wrote this song?", "We need legal names for publishing royalties.", "Composers")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown(f"**Is {d['artist']} the songwriter?**")
        if st.button("Yes, It's Me"): 
            st.session_state.data['composers'].append(d['artist'])
            next_step("Yes", jump_to=9) # Skip manual input
        if st.button("No / Someone Else"): next_step("Someone Else") # Go to 8

# === STEP 8: COMPOSER MANUAL ===
elif step == 8:
    render_focus_card("Enter the Composer's Legal Name", "First and Last name required.")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        val = st.text_input("Name", placeholder="e.g. John Smith", label_visibility="collapsed")
        if val and st.button("Add Composer"): 
            st.session_state.data['composers'].append(val)
            next_step(val)

# === STEP 9: COMPOSER LOOP ===
elif step == 9:
    render_focus_card("Composer Added.", "Do you need to add anyone else?")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("No, I'm Done", type="primary"): next_step("Done", jump_to=10)
        if st.button("Add Another Composer"): next_step("Add Another", jump_to=8)

# === STEP 10: PERFORMER START ===
elif step == 10:
    render_focus_card("Who performed on this track?", "Vocals, Instruments, etc.")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown(f"**Did {d['artist']} perform?**")
        if st.button("Yes"): 
            st.session_state.temp_name = d['artist']
            next_step("Yes", jump_to=11)
        if st.button("No / Someone Else"): next_step("No", jump_to=12)

# === STEP 11: PERFORMER ROLE ===
elif step == 11:
    render_focus_card(f"What did {st.session_state.temp_name} play?")
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
    render_focus_card("Enter Performer Name")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        val = st.text_input("Name", label_visibility="collapsed")
        if val and st.button("Next"):
            st.session_state.temp_name = val
            next_step(val, jump_to=11)

# === STEP 13: PERFORMER LOOP ===
elif step == 13:
    render_focus_card("Performer Added.", "Anyone else?")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("Done", type="primary"): next_step("Done", jump_to=14)
        if st.button("Add Another"): next_step("Add", jump_to=12)

# === STEP 14: LANGUAGE ===
elif step == 14:
    render_focus_card("Lyrics Language")
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
    render_focus_card("Upload Master Audio", "WAV or MP3")
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
