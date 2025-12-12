import streamlit as st
import time

# --- 1. SETUP & LIBRARY CHECKS ---
# We wrap imports to prevent crashing if libraries are missing
try:
    from groq import Groq
    import google.generativeai as genai
    from openai import OpenAI
except ImportError:
    st.error("⚠️ Missing AI libraries. Please run: pip install groq google-generativeai openai")

# --- 2. CONFIGURATION & STYLING ---
st.set_page_config(page_title="BandLab DistroBot V10", page_icon="🔥", layout="wide")

st.markdown("""
<style>
    /* GLOBAL THEME */
    .stApp { background-color: #ffffff; color: #222; }
    
    /* CHAT BUBBLES */
    .stChatMessage {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    /* AI BADGES */
    .model-badge {
        font-size: 0.7em;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: bold;
        display: inline-block;
        margin-top: 8px;
        font-family: monospace;
        letter-spacing: 0.5px;
    }
    .badge-groq { background: #fff3e0; color: #ef6c00; border: 1px solid #ffe0b2; }
    .badge-gemini { background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; }
    .badge-gpt { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
    .badge-sys { background: #f5f5f5; color: #616161; border: 1px solid #e0e0e0; }

    /* BANDLAB BUTTONS */
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
    
    /* TUTORIAL CARD */
    .tutorial-card {
        background: #fafafa;
        border: 1px solid #eee;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        margin-bottom: 20px;
    }
    .tutorial-icons { font-size: 2em; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 3. MULTI-MODEL AI ENGINE ---

def get_ai_response(prompt):
    """
    Tries AI models in order: Groq -> Gemini -> GPT -> Fallback.
    Returns: (text, model_name, badge_class)
    """
    system_prompt = (
        "You are DistroBot, a senior Music Distribution Expert at BandLab. "
        "Help artists with metadata, royalties, and DSP rules. "
        "Keep answers concise, helpful, and accurate."
    )

    # 1. GROQ (Llama 3.3) - Speed Layer
    if "GROQ_API_KEY" in st.secrets:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            resp = client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile", 
            )
            return resp.choices[0].message.content, "Groq (Llama 3.3)", "badge-groq"
        except Exception:
            pass # Fail silently to next model
    
    # 2. GEMINI (Flash 1.5) - Balanced Layer
    if "GEMINI_API_KEY" in st.secrets:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(system_prompt + "\n\nUser: " + prompt)
            return response.text, "Gemini 1.5", "badge-gemini"
        except Exception:
            pass

    # 3. OPENAI (GPT-4o) - Reliability Layer
    if "OPENAI_API_KEY" in st.secrets:
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content, "GPT-4o", "badge-gpt"
        except Exception:
            pass

    # 4. FALLBACK
    return "I am currently offline. Please check your API keys in .streamlit/secrets.toml", "System Offline", "badge-sys"

# --- 4. MOCK ANALYZERS (Simulated AI Tasks) ---

def analyze_cover_art():
    with st.spinner("👁️ Vision AI checking guidelines..."):
        time.sleep(1.5)
    return True, "Safe: No text or nudity detected."

def analyze_audio():
    with st.spinner("🎧 ACR Cloud scanning copyrights..."):
        time.sleep(2.0)
    return True, "Clean: No matches found in 80M+ song database."

def analyze_lyrics_whisper():
    with st.spinner("📝 Whisper AI transcribing audio..."):
        time.sleep(2.5)
    return """[Verse 1]
We building features, writing code
BandLab flow, down the road...
[Chorus]
Distribution made easy today
AI agents leading the way..."""

# --- 5. STATE MANAGEMENT ---

def init_state():
    if "step" not in st.session_state:
        st.session_state.update({
            "history": [],
            "edu_history": [{
                "role": "assistant", 
                "content": "🎓 **Education Mode Active**\n\nI am connected to Llama 3, Gemini, and GPT-4. Ask me anything about distribution, royalties, or metadata!", 
                "model": "System", 
                "badge": "badge-sys"
            }],
            "step": "INTRO", 
            "edu_mode": False, 
            "edit_mode": False, 
            "temp_name": "", 
            "lyrics_txt": "",
            "data": {
                "title": "", "ver": "", "genre": "", "upc": "", "date": "ASAP", "label": "",
                "composers": [], "performers": [], "producers": [], 
                "lang": "English", "explicit": "Clean", "isrc": "", 
                "audio": None, "cover": None
            }
        })

init_state()

# --- 6. LOGIC HELPERS ---

def add_msg(role, text, model="System", badge="badge-sys"):
    msg = {"role": role, "content": text, "model": model, "badge": badge}
    if st.session_state.edu_mode:
        st.session_state.edu_history.append(msg)
    else:
        st.session_state.history.append(msg)

def next_step(step_id, prompt):
    if st.session_state.edit_mode:
        st.session_state.edit_mode = False
        st.session_state.step = "REVIEW"
        add_msg("assistant", "✅ Updated. Returning to Review.")
    else:
        st.session_state.step = step_id
        add_msg("assistant", prompt)

def smart_add(role, is_me):
    """Handles the 'Yes, it's me' logic for any role type"""
    d = st.session_state.data
    name = "xboggdan" if is_me else "Someone Else"
    
    add_msg("user", f"Yes, I am the {role[:-1]}" if is_me else "No / Someone Else")
    
    if is_me:
        if role == "Composers": 
            d['composers'].append("xboggdan")
            next_step("S2_COMP_MORE", "Added xboggdan. Add another?")
        elif role == "Performers": 
            st.session_state.temp_name = "xboggdan"
            next_step("S2_PERF_ROLE", "What instrument?")
        elif role == "Producers": 
            st.session_state.temp_name = "xboggdan"
            next_step("S2_PROD_ROLE", "What role?")
    else:
        next_step(f"S2_{role[:4].upper()}_NAME", "Enter Legal Name:")

# --- 7. UI RENDERERS ---

def render_sidebar():
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/BandLab_Technologies_logo.svg/2560px-BandLab_Technologies_logo.svg.png", width=150)
        
        st.markdown("### 🧠 Neural Core")
        c1, c2, c3 = st.columns(3)
        c1.markdown("🟢 **Groq**")
        c2.markdown("🔵 **Gemini**")
        c3.markdown("🟣 **GPT**")
        
        st.divider()
        
        # Mode Toggle
        mode = st.toggle("🎓 Education Mode", value=st.session_state.edu_mode)
        if mode != st.session_state.edu_mode:
            st.session_state.edu_mode = mode
            st.rerun()

        if st.session_state.edu_mode:
            st.info("Ask general questions. I will answer using AI.")
        else:
            d = st.session_state.data
            st.markdown("### 📀 Live Draft")
            if d['title']:
                st.write(f"**{d['title']}**")
                st.caption(f"Artist: xboggdan")
                st.caption(f"Genre: {d['genre']}")
            else:
                st.caption("No data yet.")
        
        if st.button("Reset Session"):
            st.session_state.clear()
            st.rerun()

def render_chat(history):
    for msg in history:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])
            if msg.get('model'):
                st.markdown(f"<span class='model-badge {msg['badge']}'>⚡ {msg['model']}</span>", unsafe_allow_html=True)

def render_tutorial():
    st.markdown("""
    <div class="tutorial-card">
        <div class="tutorial-icons">👁️ 🎧 📝</div>
        <h2>Welcome to DistroBot AI</h2>
        <p>This is your automated A&R agent. I will help you release music without rejection.</p>
        <div style="display:flex; justify-content:center; gap:20px; margin-top:20px;">
            <div><b>Smart Auto-Fill</b><br>Skip typing names</div>
            <div><b>AI Guardrails</b><br>Detect bad artwork</div>
            <div><b>Lyrics Engine</b><br>Auto-transcription</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🚀 Start New Release", use_container_width=True):
            st.session_state.step = "S1_TITLE"
            add_msg("assistant", "Let's go. **Step 1:** What is the **Release Title**?")
            st.rerun()

# --- 8. MAIN APP LOGIC ---

render_sidebar()

# MODE A: EDUCATION
if st.session_state.edu_mode:
    st.title("🎓 Knowledge Base")
    render_chat(st.session_state.edu_history)
    
    user_q = st.chat_input("Ask about Royalties, ISRC, etc...")
    if user_q:
        add_msg("user", user_q)
        # Call AI
        resp, model, badge = get_ai_response(user_q)
        add_msg("assistant", resp, model, badge)
        st.rerun()

# MODE B: RELEASE WIZARD
else:
    st.title("BandLab Distribution AI")
    
    if st.session_state.step == "INTRO":
        render_tutorial()
    
    else:
        render_chat(st.session_state.history)
        
        step = st.session_state.step
        d = st.session_state.data
        
        # --- INPUTS ---
        
        if step == "S1_TITLE":
            st.chat_input("Track Title...", key="i", on_submit=lambda: (d.update({"title": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S1_VER", "Version? (Original, Remix...)")))
        
        elif step == "S1_VER":
            if st.button("Original / No Version"): add_msg("user", "Original"); next_step("S1_GENRE", "Select Genre:")
            st.chat_input("Version...", key="i", on_submit=lambda: (d.update({"ver": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S1_GENRE", "Select Genre:")))

        elif step == "S1_GENRE":
            for g in ["Hip Hop", "Pop", "Rock", "R&B", "Electronic"]:
                if st.button(g, use_container_width=True): d['genre'] = g; add_msg("user", g); next_step("S1_DATE", "Release Date?")

        elif step == "S1_DATE":
            if st.button("ASAP"): d['date'] = "ASAP"; add_msg("user", "ASAP"); next_step("S1_UPC", "Do you have a UPC?")
            
        elif step == "S1_UPC":
            if st.button("Generate Free UPC"): d['upc'] = "AUTO"; add_msg("user", "Free UPC"); next_step("S1_LABEL", "Record Label Name?")
            st.chat_input("UPC...", key="i", on_submit=lambda: (d.update({"upc": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S1_LABEL", "Record Label Name?")))

        elif step == "S1_LABEL":
            if st.button("Use Artist Name"): d['label'] = "xboggdan"; add_msg("user", "xboggdan"); next_step("S2_COMP_START", "Composers: Is **xboggdan** the composer?")
            st.chat_input("Label...", key="i", on_submit=lambda: (d.update({"label": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S2_COMP_START", "Composers: Is **xboggdan** the composer?")))

        # --- SMART ROLES ---
        elif step == "S2_COMP_START":
            c1, c2 = st.columns(2)
            if c1.button("Yes"): smart_add("Composers", True); st.rerun()
            if c2.button("No"): smart_add("Composers", False); st.rerun()

        elif step == "S2_COMP_NAME":
            st.chat_input("Name...", key="i", on_submit=lambda: (d['composers'].append(st.session_state.i), add_msg("user", st.session_state.i), next_step("S2_COMP_MORE", "Add another?")))
            
        elif step == "S2_COMP_MORE":
            if st.button("Done"): next_step("S2_PERF_START", "Performers: Did **xboggdan** perform?"); st.rerun()
            if st.button("Add Another"): next_step("S2_COMP_NAME", "Enter Name:"); st.rerun()

        elif step == "S2_PERF_START":
            c1, c2 = st.columns(2)
            if c1.button("Yes"): smart_add("Performers", True); st.rerun()
            if c2.button("No"): smart_add("Performers", False); st.rerun()
            
        elif step == "S2_PERF_NAME":
            st.chat_input("Name...", key="i", on_submit=lambda: (setattr(st.session_state, 'temp_name', st.session_state.i), add_msg("user", st.session_state.i), next_step("S2_PERF_ROLE", "Instrument?")))

        elif step == "S2_PERF_ROLE":
            for i in ["Vocals", "Guitar", "Keys", "Drums"]:
                if st.button(i, use_container_width=True): d['performers'].append({"name": st.session_state.temp_name, "role": i}); add_msg("user", i); next_step("S2_PERF_MORE", "Add another?")
        
        elif step == "S2_PERF_MORE":
            if st.button("Done"): next_step("S2_PROD_START", "Producers: Is **xboggdan** the producer?"); st.rerun()
            if st.button("Add Another"): next_step("S2_PERF_NAME", "Enter Name:"); st.rerun()

        elif step == "S2_PROD_START":
            c1, c2 = st.columns(2)
            if c1.button("Yes"): smart_add("Producers", True); st.rerun()
            if c2.button("No"): smart_add("Producers", False); st.rerun()

        elif step == "S2_PROD_NAME":
             st.chat_input("Name...", key="i", on_submit=lambda: (setattr(st.session_state, 'temp_name', st.session_state.i), add_msg("user", st.session_state.i), next_step("S2_PROD_ROLE", "Role?")))

        elif step == "S2_PROD_ROLE":
            for i in ["Producer", "Mixing Engineer"]:
                if st.button(i, use_container_width=True): 
                    d['producers'].append({"name": st.session_state.temp_name, "role": i})
                    add_msg("user", i)
                    # FIXED LOGIC: MOVES TO LYRICS
                    next_step("S2_LANG", "Select **Lyrics Language**:") 
                    st.rerun()

        # --- LYRICS & FILES ---
        elif step == "S2_LANG":
            if st.button("English"): d['lang'] = "English"; add_msg("user", "English"); next_step("S2_EXPL", "Is it **Explicit**?")
            if st.button("Instrumental"): d['lang'] = "Instrumental"; add_msg("user", "Instrumental"); next_step("S2_ISRC", "Do you have an ISRC?")

        elif step == "S2_EXPL":
            if st.button("Clean"): d['explicit'] = "Clean"; add_msg("user", "Clean"); next_step("S2_ISRC", "Do you have an ISRC?")
            if st.button("Explicit"): d['explicit'] = "Explicit"; add_msg("user", "Explicit"); next_step("S2_ISRC", "Do you have an ISRC?")

        elif step == "S2_ISRC":
            if st.button("Generate Free ISRC"): d['isrc'] = "AUTO"; add_msg("user", "Free ISRC"); next_step("S3_COVER", "Upload **Cover Art**")
            st.chat_input("ISRC...", key="i", on_submit=lambda: (d.update({"isrc": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S3_COVER", "Upload **Cover Art**")))

        elif step == "S3_COVER":
            f = st.file_uploader("Cover Art", type=["jpg", "png"])
            if f:
                d['cover'] = f; add_msg("user", "Uploaded Art")
                safe, reason = analyze_cover_art()
                next_step("S3_AUDIO", f"✅ {reason}\n\nUpload **Audio**.")
                st.rerun()

        elif step == "S3_AUDIO":
            f = st.file_uploader("Audio", type=["wav", "mp3"])
            if f:
                d['audio'] = f; add_msg("user", "Uploaded Audio")
                safe, reason = analyze_audio()
                if d['lang'] == "Instrumental":
                    next_step("REVIEW", f"✅ {reason}\n\nReview Release.")
                else:
                    next_step("S3_LYRICS", f"✅ {reason}\n\nTranscribing Lyrics...")
                st.rerun()

        elif step == "S3_LYRICS":
            txt = analyze_lyrics_whisper()
            st.session_state.lyrics_txt = txt
            next_step("S3_LYRICS_EDIT", "Please confirm lyrics:")
            st.rerun()

        elif step == "S3_LYRICS_EDIT":
            v = st.text_area("Edit Lyrics", value=st.session_state.lyrics_txt)
            if st.button("Confirm"): next_step("REVIEW", "Done! Review below.")

        elif step == "REVIEW":
            st.subheader("💿 Release Summary")
            st.write(d)
            if st.button("🚀 SUBMIT"): st.balloons(); st.success("Submitted!")
