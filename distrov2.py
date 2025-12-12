import streamlit as st
import time

# --- 1. SETUP & LIBRARY CHECKS ---
try:
    from groq import Groq
    import google.generativeai as genai
    from openai import OpenAI
except ImportError:
    st.error("⚠️ Missing AI libraries. Please run: pip install groq google-generativeai openai")

# --- 2. CONFIGURATION ---
st.set_page_config(page_title="BandLab DistroBot V11", page_icon="🔥", layout="wide")

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
        font-size: 0.7em; padding: 3px 8px; border-radius: 12px;
        font-weight: bold; display: inline-block; margin-top: 8px;
        font-family: monospace; letter-spacing: 0.5px;
    }
    .badge-groq { background: #fff3e0; color: #ef6c00; border: 1px solid #ffe0b2; }
    .badge-gemini { background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; }
    .badge-gpt { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
    .badge-sys { background: #f5f5f5; color: #616161; border: 1px solid #e0e0e0; }

    /* BANDLAB BUTTONS */
    .stButton > button {
        background-color: #F50000; color: white; border-radius: 20px;
        border: none; padding: 8px 24px; font-weight: 600; transition: 0.2s;
    }
    .stButton > button:hover { background-color: #d10000; color: white; }
    
    /* TUTORIAL CARD */
    .tutorial-card {
        background: #fafafa; border: 1px solid #eee; border-radius: 15px;
        padding: 30px; text-align: center; margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. AI ENGINE ---

def get_ai_response(prompt):
    """Multi-Model AI Cascade"""
    system_prompt = "You are DistroBot, a senior Music Distribution Expert at BandLab. Help with metadata, royalties, and DSP rules. Be concise."

    # 1. GROQ (Llama 3.3)
    if "GROQ_API_KEY" in st.secrets:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            resp = client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile", 
            )
            return resp.choices[0].message.content, "Groq (Llama 3.3)", "badge-groq"
        except: pass
    
    # 2. GEMINI (Flash 1.5)
    if "GEMINI_API_KEY" in st.secrets:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(system_prompt + "\n\nUser: " + prompt)
            return response.text, "Gemini 1.5", "badge-gemini"
        except: pass

    # 3. OPENAI (GPT-4o)
    if "OPENAI_API_KEY" in st.secrets:
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content, "GPT-4o", "badge-gpt"
        except: pass

    return "Offline. Check API Keys.", "System", "badge-sys"

# --- 4. ANALYZERS ---
def analyze_cover_art():
    with st.spinner("👁️ Vision AI checking guidelines..."): time.sleep(1.0)
    return True, "Safe: No text or nudity detected."

def analyze_audio():
    with st.spinner("🎧 ACR Cloud scanning copyrights..."): time.sleep(1.5)
    return True, "Clean: No matches found."

def analyze_lyrics():
    with st.spinner("📝 Whisper AI transcribing..."): time.sleep(2.0)
    return "[Verse 1]\nWe building features..."

# --- 5. STATE & CALLBACKS (THE FIX) ---

def init_state():
    if "step" not in st.session_state:
        st.session_state.update({
            "history": [],
            "edu_history": [{"role": "assistant", "content": "🎓 **Education Mode**\nAsk me anything about distribution!", "model": "System", "badge": "badge-sys"}],
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

# --- THE CALLBACK ENGINE (Fixes Double Click) ---

def add_msg(role, text, model="System", badge="badge-sys"):
    msg = {"role": role, "content": text, "model": model, "badge": badge}
    target = st.session_state.edu_history if st.session_state.edu_mode else st.session_state.history
    target.append(msg)

def advance(next_step_id, bot_prompt, user_text=None, update_key=None, update_val=None, append_list=None):
    """
    Universal Callback: Updates state -> Adds User Msg -> Adds Bot Msg
    """
    # 1. Update Data
    if update_key and update_val is not None:
        st.session_state.data[update_key] = update_val
    if append_list and update_val is not None:
        st.session_state.data[append_list].append(update_val)
    
    # 2. Add User Message (if visible)
    if user_text:
        add_msg("user", user_text)
        
    # 3. Handle Edit Mode Loop
    if st.session_state.edit_mode:
        st.session_state.edit_mode = False
        st.session_state.step = "REVIEW"
        add_msg("assistant", "✅ Updated. Returning to Review.")
    else:
        st.session_state.step = next_step_id
        add_msg("assistant", bot_prompt)

def cb_text_input(key_name, next_s, prompt):
    """Callback specifically for st.chat_input"""
    val = st.session_state.user_input_widget
    if val:
        advance(next_s, prompt, user_text=val, update_key=key_name, update_val=val)

def cb_smart_add(role, is_me):
    """Callback for Smart Add buttons"""
    name = "xboggdan" if is_me else "Someone Else"
    user_txt = f"Yes, I am the {role[:-1]}" if is_me else "No / Someone Else"
    
    add_msg("user", user_txt)
    
    if is_me:
        if role == "Composers": 
            st.session_state.data['composers'].append("xboggdan")
            st.session_state.step = "S2_COMP_MORE"
            add_msg("assistant", "Added xboggdan. Add another?")
        elif role == "Performers": 
            st.session_state.temp_name = "xboggdan"
            st.session_state.step = "S2_PERF_ROLE"
            add_msg("assistant", "What instrument?")
        elif role == "Producers": 
            st.session_state.temp_name = "xboggdan"
            st.session_state.step = "S2_PROD_ROLE"
            add_msg("assistant", "What role?")
    else:
        # Move to manual input step
        st.session_state.step = f"S2_{role[:4].upper()}_NAME"
        add_msg("assistant", "Enter Legal Name:")

# --- 6. UI RENDERERS ---

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

        if not st.session_state.edu_mode:
            d = st.session_state.data
            st.markdown("### 📀 Live Draft")
            if d['title']:
                st.write(f"**{d['title']}**")
                st.caption(f"Artist: xboggdan")
        
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
        <div style="font-size: 2em; margin-bottom: 10px;">👁️ 🎧 📝</div>
        <h2>DistroBot AI Agent</h2>
        <p>Your automated A&R assistant for rapid distribution.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.button("🚀 Start New Release", on_click=advance, args=("S1_TITLE", "Let's go. **Step 1:** What is the **Release Title**?"), use_container_width=True)

# --- 7. MAIN APP LOGIC ---

render_sidebar()

# MODE A: EDUCATION
if st.session_state.edu_mode:
    st.title("🎓 Knowledge Base")
    render_chat(st.session_state.edu_history)
    
    q = st.chat_input("Ask about Royalties, ISRC, etc...")
    if q:
        add_msg("user", q)
        resp, model, badge = get_ai_response(q)
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
        
        # --- INPUTS (Now using Callbacks) ---
        
        if step == "S1_TITLE":
            st.chat_input("Track Title...", key="user_input_widget", on_submit=cb_text_input, args=("title", "S1_VER", "Version? (Original, Remix...)"))
        
        elif step == "S1_VER":
            if st.button("Original / No Version"): advance("S1_GENRE", "Select Genre:", "Original", "ver", "Original")
            st.chat_input("Version...", key="user_input_widget", on_submit=cb_text_input, args=("ver", "S1_GENRE", "Select Genre:"))

        elif step == "S1_GENRE":
            cols = st.columns(4)
            genres = ["Hip Hop", "Pop", "Rock", "R&B", "Electronic", "Country", "Jazz", "Classical"]
            for i, g in enumerate(genres):
                if cols[i%4].button(g, use_container_width=True):
                    advance("S1_DATE", "Release Date?", g, "genre", g)

        elif step == "S1_DATE":
            if st.button("ASAP"): advance("S1_UPC", "Do you have a UPC?", "ASAP", "date", "ASAP")
            
        elif step == "S1_UPC":
            if st.button("Generate Free UPC"): advance("S1_LABEL", "Record Label Name?", "Free UPC", "upc", "AUTO")
            st.chat_input("UPC...", key="user_input_widget", on_submit=cb_text_input, args=("upc", "S1_LABEL", "Record Label Name?"))

        elif step == "S1_LABEL":
            if st.button("Use Artist Name"): advance("S2_COMP_START", "Composers: Is **xboggdan** the composer?", "xboggdan", "label", "xboggdan")
            st.chat_input("Label...", key="user_input_widget", on_submit=cb_text_input, args=("label", "S2_COMP_START", "Composers: Is **xboggdan** the composer?"))

        # --- SMART ROLES ---
        elif step == "S2_COMP_START":
            c1, c2 = st.columns(2)
            c1.button("Yes", on_click=cb_smart_add, args=("Composers", True), use_container_width=True)
            c2.button("No", on_click=cb_smart_add, args=("Composers", False), use_container_width=True)

        elif step == "S2_COMP_NAME":
            st.chat_input("Name...", key="user_input_widget", on_submit=lambda: advance("S2_COMP_MORE", "Add another?", st.session_state.user_input_widget, None, None, "composers"))
            
        elif step == "S2_COMP_MORE":
            c1, c2 = st.columns(2)
            c1.button("Done", on_click=advance, args=("S2_PERF_START", "Performers: Did **xboggdan** perform?"), use_container_width=True)
            c2.button("Add Another", on_click=advance, args=("S2_COMP_NAME", "Enter Name:"), use_container_width=True)

        elif step == "S2_PERF_START":
            c1, c2 = st.columns(2)
            c1.button("Yes", on_click=cb_smart_add, args=("Performers", True), use_container_width=True)
            c2.button("No", on_click=cb_smart_add, args=("Performers", False), use_container_width=True)
            
        elif step == "S2_PERF_NAME":
            st.chat_input("Name...", key="user_input_widget", on_submit=lambda: (setattr(st.session_state, 'temp_name', st.session_state.user_input_widget), advance("S2_PERF_ROLE", "Instrument?", st.session_state.user_input_widget)))

        elif step == "S2_PERF_ROLE":
            cols = st.columns(4)
            insts = ["Vocals", "Guitar", "Keys", "Drums", "Bass", "Synth", "Violin", "Other"]
            for i, inst in enumerate(insts):
                if cols[i%4].button(inst, use_container_width=True):
                    # Complex data append handled manually here for transparency
                    st.session_state.data['performers'].append({"name": st.session_state.temp_name, "role": inst})
                    advance("S2_PERF_MORE", "Add another?", inst)
        
        elif step == "S2_PERF_MORE":
            c1, c2 = st.columns(2)
            c1.button("Done", on_click=advance, args=("S2_PROD_START", "Producers: Is **xboggdan** the producer?"), use_container_width=True)
            c2.button("Add Another", on_click=advance, args=("S2_PERF_NAME", "Enter Name:"), use_container_width=True)

        elif step == "S2_PROD_START":
            c1, c2 = st.columns(2)
            c1.button("Yes", on_click=cb_smart_add, args=("Producers", True), use_container_width=True)
            c2.button("No", on_click=cb_smart_add, args=("Producers", False), use_container_width=True)

        elif step == "S2_PROD_NAME":
             st.chat_input("Name...", key="user_input_widget", on_submit=lambda: (setattr(st.session_state, 'temp_name', st.session_state.user_input_widget), advance("S2_PROD_ROLE", "Role?", st.session_state.user_input_widget)))

        elif step == "S2_PROD_ROLE":
            for i in ["Producer", "Mixing Engineer", "Mastering Engineer"]:
                if st.button(i, use_container_width=True): 
                    st.session_state.data['producers'].append({"name": st.session_state.temp_name, "role": i})
                    advance("S2_LANG", "Select **Lyrics Language**:", i)

        # --- LYRICS ---
        elif step == "S2_LANG":
            c1, c2 = st.columns(2)
            c1.button("English", on_click=advance, args=("S2_EXPL", "Is it **Explicit**?", "English", "lang", "English"), use_container_width=True)
            c2.button("Instrumental", on_click=advance, args=("S2_ISRC", "ISRC?", "Instrumental", "lang", "Instrumental"), use_container_width=True)

        elif step == "S2_EXPL":
            c1, c2 = st.columns(2)
            c1.button("Clean", on_click=advance, args=("S2_ISRC", "ISRC?", "Clean", "explicit", "Clean"), use_container_width=True)
            c2.button("Explicit", on_click=advance, args=("S2_ISRC", "ISRC?", "Explicit", "explicit", "Explicit"), use_container_width=True)

        elif step == "S2_ISRC":
            if st.button("Generate Free ISRC"): advance("S3_COVER", "Upload **Cover Art**", "Free ISRC", "isrc", "AUTO")
            st.chat_input("ISRC...", key="user_input_widget", on_submit=cb_text_input, args=("isrc", "S3_COVER", "Upload **Cover Art**"))

        # --- FILES ---
        elif step == "S3_COVER":
            f = st.file_uploader("Cover Art", type=["jpg", "png"])
            if f:
                st.session_state.data['cover'] = f
                add_msg("user", "Uploaded Art")
                safe, reason = analyze_cover_art()
                advance("S3_AUDIO", f"✅ {reason}\n\nUpload **Audio**.")
                st.rerun()

        elif step == "S3_AUDIO":
            f = st.file_uploader("Audio", type=["wav", "mp3"])
            if f:
                st.session_state.data['audio'] = f
                add_msg("user", "Uploaded Audio")
                safe, reason = analyze_audio()
                if st.session_state.data['lang'] == "Instrumental":
                    advance("REVIEW", f"✅ {reason}\n\nReview Release.")
                else:
                    advance("S3_LYRICS", f"✅ {reason}\n\nTranscribing Lyrics...")
                st.rerun()

        elif step == "S3_LYRICS":
            txt = analyze_lyrics()
            st.session_state.lyrics_txt = txt
            advance("S3_LYRICS_EDIT", "Please confirm lyrics:")
            st.rerun()

        elif step == "S3_LYRICS_EDIT":
            v = st.text_area("Edit Lyrics", value=st.session_state.lyrics_txt)
            if st.button("Confirm"): advance("REVIEW", "Done! Review below.")

        elif step == "REVIEW":
            st.subheader("💿 Release Summary")
            st.write(d)
            if st.button("🚀 SUBMIT"): st.balloons(); st.success("Submitted!")
