import streamlit as st
import time
import uuid

# --- 1. SETUP & IMPORTS ---
try:
    from groq import Groq
    import google.generativeai as genai
    from openai import OpenAI
except ImportError:
    pass # We handle missing libs gracefully in the AI function

# --- 2. CONFIGURATION & CSS ---
st.set_page_config(page_title="BandLab Distribution", page_icon="🔥", layout="centered")

st.markdown("""
<style>
    /* BANDLAB CLEAN THEME */
    .stApp { background-color: #FFFFFF; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Chat Message Styling */
    .user-msg {
        background-color: #F50000; color: white; 
        padding: 10px 15px; border-radius: 15px 15px 0 15px;
        margin: 5px 0 5px auto; max-width: 80%; width: fit-content;
        box-shadow: 0 2px 5px rgba(245,0,0,0.2);
    }
    .bot-msg {
        background-color: #F3F4F6; color: #1F2937;
        padding: 10px 15px; border-radius: 15px 15px 15px 0;
        margin: 5px auto 5px 0; max-width: 80%; width: fit-content;
        border: 1px solid #E5E7EB;
    }
    
    /* Input Area Styling */
    .input-container {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background: white; padding: 20px; border-top: 1px solid #eee;
        z-index: 999;
    }
    
    /* Button Styling */
    .stButton > button {
        border-radius: 12px; font-weight: 600; padding: 0.5rem 1rem;
        border: 1px solid #eee; background-color: white; color: #333;
        transition: all 0.2s; width: 100%;
    }
    .stButton > button:hover {
        border-color: #F50000; color: #F50000; background-color: #FFF5F5;
    }
    /* Primary Action Button (used for 'Next', 'Confirm') */
    .primary-btn > button {
        background-color: #F50000 !important; color: white !important; border: none !important;
    }
    
    /* AI Badge */
    .ai-badge { font-size: 0.65em; opacity: 0.7; margin-left: 8px; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# --- 3. AI ENGINE (ROBUST) ---

def ask_ai(prompt):
    """
    Returns (Response_Text, Badge_HTML)
    Tries connected AIs, falls back to static logic if offline.
    """
    sys_prompt = "You are a helpful music distribution assistant."
    
    # GROQ
    if "GROQ_API_KEY" in st.secrets:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            res = client.chat.completions.create(
                messages=[{"role":"system","content":sys_prompt},{"role":"user","content":prompt}],
                model="llama-3.3-70b-versatile"
            )
            return res.choices[0].message.content, "⚡ Llama 3"
        except: pass

    # GEMINI
    if "GEMINI_API_KEY" in st.secrets:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(prompt)
            return res.text, "✨ Gemini"
        except: pass

    # OPENAI
    if "OPENAI_API_KEY" in st.secrets:
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role":"system","content":sys_prompt},{"role":"user","content":prompt}]
            )
            return res.choices[0].message.content, "🧠 GPT-4"
        except: pass

    # FALLBACK (No API Key)
    return None, "⚙️ Logic" # Return None to let the app handle static text

def get_edu_info(topic):
    ai_resp, badge = ask_ai(f"Explain what {topic} is in music distribution in 1 short sentence.")
    if ai_resp: return ai_resp, badge
    
    # Fallback Dict
    kb = {
        "UPC": "Universal Product Code: A barcode that tracks sales of your release.",
        "ISRC": "International Standard Recording Code: The unique fingerprint for your audio track.",
        "Explicit": "Mark 'Explicit' if lyrics contain profanity, violence, or drug references."
    }
    return kb.get(topic, "Distribution Metadata"), "⚙️ Logic"

# --- 4. STATE MANAGEMENT ---

def init():
    if "session_id" not in st.session_state:
        st.session_state.update({
            "session_id": str(uuid.uuid4()),
            "step": 1, # Numeric step for linear progression
            "history": [], # Chat log
            "edu_mode": False,
            # The Data Payload
            "data": {
                "title": "", "version": "", "artist": "xboggdan", "genre": "", 
                "date": "ASAP", "label": "", "upc": "",
                "composers": [], "performers": [], "producers": [],
                "lang": "English", "explicit": "Clean", "isrc": "",
                "cover": None, "audio": None
            },
            # Temp holders for loop flows
            "temp_name": "", "temp_role": ""
        })
        # Add Welcome Message
        add_msg("assistant", "🔥 **Welcome to BandLab Distribution.**\n\nI'll help you get your music on Spotify. Let's start with the **Release Details**.")
        add_msg("assistant", "What is the **Release Title**?")

def add_msg(role, text, badge=""):
    st.session_state.history.append({"role": role, "text": text, "badge": badge})

def go_next(user_text=None, set_key=None, set_val=None):
    """
    Universal Advance Function
    1. Records User Answer
    2. Updates Data Payload
    3. Increments Step
    4. Reruns app to show next question
    """
    if user_text:
        add_msg("user", user_text)
    
    if set_key and set_val is not None:
        st.session_state.data[set_key] = set_val
    
    st.session_state.step += 1
    st.rerun()

# --- 5. LOGIC FLOW (THE STEPS) ---

def render_step_logic():
    step = st.session_state.step
    d = st.session_state.data
    
    # === STEP 1: RELEASE INFO ===
    if step == 1: # Title is handled in init
        with st.container():
            val = st.text_input("Release Title", placeholder="e.g. Summer Vibes", key=f"in_{step}")
            if st.button("Next ➝", type="primary", use_container_width=True):
                if val: go_next(val, "title", val)

    elif step == 2:
        if len(st.session_state.history) < 3: add_msg("assistant", "Any **Version** info? (e.g. Radio Edit, Remix)")
        c1, c2 = st.columns(2)
        if c1.button("Original Mix (Skip)"): go_next("Original Mix", "version", "")
        with c2:
            val = st.text_input("Version", placeholder="e.g. Acoustic", label_visibility="collapsed", key=f"in_{step}")
            if val and st.button("Set Version"): go_next(val, "version", val)

    elif step == 3:
        if len(st.session_state.history) < 5: add_msg("assistant", "Select your **Genre**.")
        genres = ["Hip Hop", "Pop", "Rock", "R&B", "Electronic", "Alternative", "Country", "Latin"]
        cols = st.columns(4)
        for i, g in enumerate(genres):
            if cols[i%4].button(g, use_container_width=True):
                go_next(g, "genre", g)

    elif step == 4:
        if len(st.session_state.history) < 7: add_msg("assistant", "When should we release this?")
        c1, c2 = st.columns(2)
        if c1.button("ASAP (As soon as possible)", use_container_width=True):
            go_next("ASAP", "date", "ASAP")
        with c2:
            date_val = st.date_input("Pick Date", label_visibility="collapsed")
            if st.button("Confirm Date"): go_next(str(date_val), "date", str(date_val))

    elif step == 5:
        if len(st.session_state.history) < 9: 
            msg, badge = get_edu_info("UPC")
            add_msg("assistant", f"Do you have a **UPC**?\n\n*💡 {msg}*", badge)
            
        c1, c2 = st.columns(2)
        if c1.button("Generate Free UPC", use_container_width=True):
            go_next("Generate for me", "upc", "AUTO")
        with c2:
            val = st.text_input("UPC", placeholder="12-13 Digits", label_visibility="collapsed", key=f"in_{step}")
            if val and st.button("Set UPC"): go_next(val, "upc", val)

    elif step == 6:
        if len(st.session_state.history) < 11: add_msg("assistant", "Record **Label** Name?")
        c1, c2 = st.columns(2)
        if c1.button(f"Use '{d['artist']}'", use_container_width=True):
            go_next(d['artist'], "label", d['artist'])
        with c2:
            val = st.text_input("Label", placeholder="Label Name", label_visibility="collapsed", key=f"in_{step}")
            if val and st.button("Set Label"): go_next(val, "label", val)

    # === STEP 2: TRACK ROLES (The Smart Logic) ===
    
    elif step == 7: # COMPOSER START
        if len(st.session_state.history) < 13: 
            add_msg("assistant", "Let's add Credits. **Composers** (Songwriters).")
            add_msg("assistant", f"Is **{d['artist']}** the composer?")
        
        c1, c2 = st.columns(2)
        if c1.button("Yes, it's me", type="primary", use_container_width=True):
            st.session_state.data['composers'].append(d['artist'])
            go_next("Yes, I am the composer") # Jumps to step 8
        if c2.button("No / Someone Else", use_container_width=True):
            go_next("Someone Else") # Jumps to step 8

    elif step == 8: # COMPOSER ADD MORE LOOP
        # Check if we just added someone, or need to ask for name
        last_msg = st.session_state.history[-1]['text']
        
        if last_msg == "Someone Else" or last_msg == "Add Another":
            st.text_input("Legal First & Last Name", key="comp_input", on_change=lambda: add_list_item("composers", st.session_state.comp_input, 8))
        else:
            # We just added someone
            st.success("Composer Added.")
            add_msg("assistant", "Add another composer?")
            c1, c2 = st.columns(2)
            if c1.button("No, Done"): 
                st.session_state.step = 9 # Go to Performers
                st.rerun()
            if c2.button("Add Another"):
                add_msg("user", "Add Another")
                st.rerun()
