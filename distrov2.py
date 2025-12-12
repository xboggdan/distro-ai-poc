import streamlit as st
import time

# --- IMPORTS FOR AI CLIENTS ---
try:
    from groq import Groq
    import google.generativeai as genai
    from openai import OpenAI
except ImportError:
    st.error("⚠️ Missing AI libraries. Please run: pip install groq google-generativeai openai")

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="BandLab DistroBot V9", page_icon="🔥", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #ffffff; color: #222; }
    .stChatMessage { background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 12px; padding: 15px; }
    .stButton > button { background-color: #F50000; color: white; border-radius: 20px; border: none; padding: 8px 24px; font-weight: 600; }
    .stButton > button:hover { background-color: #d10000; color: white; }
    .model-badge { font-size: 0.7em; padding: 3px 8px; border-radius: 12px; font-weight: bold; display: inline-block; margin-top: 8px; font-family: monospace; }
    .badge-groq { background: #ffecb3; color: #ff6f00; border: 1px solid #ffca28; }
    .badge-gemini { background: #e3f2fd; color: #0277bd; border: 1px solid #81d4fa; }
    .badge-gpt { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
    .badge-fallback { background: #f5f5f5; color: #616161; border: 1px solid #e0e0e0; }
</style>
""", unsafe_allow_html=True)

# --- 2. AI ENGINE (UPDATED MODELS) ---

def get_ai_response(prompt):
    """
    Tries AI models in order: Groq -> Gemini -> GPT -> Fallback.
    """
    system_prompt = "You are DistroBot, a BandLab Distribution Expert. Help artists with metadata, royalties, and DSP rules. Be concise."

    # 1. GROQ (Updated to Llama 3.3)
    if "GROQ_API_KEY" in st.secrets:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            chat_completion = client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile", 
            )
            return chat_completion.choices[0].message.content, "Groq (Llama 3.3)", "badge-groq"
        except Exception:
            pass
    
    # 2. GEMINI (Updated to Flash 1.5)
    if "GEMINI_API_KEY" in st.secrets:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(system_prompt + "\n\nUser: " + prompt)
            return response.text, "Gemini 1.5", "badge-gemini"
        except Exception:
            pass

    # 3. OPENAI
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

    return "I am offline. Please check your API keys.", "System", "badge-fallback"

# --- 3. MOCK FILE CHECKS ---
def check_cover():
    with st.spinner("👁️ Vision AI checking guidelines..."): time.sleep(1.5)
    return True, "Safe: No text/nudity detected."

def check_audio():
    with st.spinner("🎧 ACR Cloud scanning copyrights..."): time.sleep(2.0)
    return True, "Clean: No matches found."

def check_lyrics():
    with st.spinner("📝 Whisper AI transcribing..."): time.sleep(2.0)
    return "[Verse 1]\nBandLab on the track...\n[Chorus]\nWe going global..."

# --- 4. STATE ---
def init_state():
    if "step" not in st.session_state:
        st.session_state.update({
            "history": [],
            "edu_history": [{"role": "assistant", "content": "🎓 **Education Mode**\n\nAsk me about royalties, UPCs, or cover art rules.", "model": "System", "badge": "badge-fallback"}],
            "step": "INTRO", "edu_mode": False, "edit_mode": False, "temp_name": "", "lyrics_txt": "",
            "data": {
                "title": "", "ver": "", "genre": "", "upc": "", "date": "ASAP", "label": "",
                "composers": [], "performers": [], "producers": [], 
                "lang": "English", "explicit": "Clean", "isrc": "", 
                "audio": None, "cover": None
            }
        })
init_state()

# --- 5. LOGIC HANDLERS ---
def add_msg(role, text, model="System", badge="badge-fallback"):
    msg = {"role": role, "content": text, "model": model, "badge": badge}
    target = st.session_state.edu_history if st.session_state.edu_mode else st.session_state.history
    target.append(msg)

def next_step(step_id, prompt):
    if st.session_state.edit_mode:
        st.session_state.edit_mode = False
        st.session_state.step = "REVIEW"
        add_msg("assistant", "✅ Updated. Returning to Review.")
    else:
        st.session_state.step = step_id
        add_msg("assistant", prompt)

def smart_add(role, is_me):
    d = st.session_state.data
    name = "xboggdan" if is_me else "Someone Else"
    add_msg("user", f"Yes, I am the {role[:-1]}" if is_me else "No / Someone Else")
    
    if is_me:
        if role == "Composers": d['composers'].append("xboggdan"); next_step("S2_COMP_MORE", "Added xboggdan. Add another?")
        elif role == "Performers": st.session_state.temp_name = "xboggdan"; next_step("S2_PERF_ROLE", "Instrument?")
        elif role == "Producers": st.session_state.temp_name = "xboggdan"; next_step("S2_PROD_ROLE", "Role?")
    else:
        next_step(f"S2_{role[:4].upper()}_NAME", "Enter Name:")

# --- 6. UI ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/BandLab_Technologies_logo.svg/2560px-BandLab_Technologies_logo.svg.png", width=150)
    st.markdown("### 🧠 AI Status")
    if "GROQ_API_KEY" in st.secrets: st.success("Groq Connected")
    if "GEMINI_API_KEY" in st.secrets: st.success("Gemini Connected")
    
    st.divider()
    mode = st.toggle("🎓 Education Mode", value=st.session_state.edu_mode)
    if mode != st.session_state.edu_mode: st.session_state.edu_mode = mode; st.rerun()

    if st.button("Reset"): st.session_state.clear(); st.rerun()

def render_chat(history):
    for msg in history:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])
            if msg.get('model'): st.markdown(f"<span class='model-badge {msg['badge']}'>⚡ {msg['model']}</span>", unsafe_allow_html=True)

# --- 7. MAIN APP ---
if st.session_state.edu_mode:
    st.title("🎓 Knowledge Base")
    render_chat(st.session_state.edu_history)
    q = st.chat_input("Ask a question...")
    if q:
        add_msg("user", q)
        resp, model, badge = get_ai_response(q)
        add_msg("assistant", resp, model, badge)
        st.rerun()
else:
    st.title("BandLab Distribution AI")
    if st.session_state.step == "INTRO":
        if st.button("🔥 Start Release", use_container_width=True):
            st.session_state.step = "S1_TITLE"
            add_msg("assistant", "Let's go. **Step 1:** What is the **Release Title**?")
            st.rerun()
    else:
        render_chat(st.session_state.history)
        step = st.session_state.step
        d = st.session_state.data
        
        # --- INPUTS ---
        if step == "S1_TITLE":
            st.chat_input("Title...", key="i", on_submit=lambda: (d.update({"title": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S1_VER", "Version? (Original, Remix...)")))
        
        elif step == "S1_VER":
            if st.button("Original"): add_msg("user", "Original"); next_step("S1_GENRE", "Select Genre:")
            st.chat_input("Version...", key="i", on_submit=lambda: (d.update({"ver": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S1_GENRE", "Select Genre:")))

        elif step == "S1_GENRE":
            for g in ["Hip Hop", "Pop", "Rock", "R&B"]:
                if st.button(g, use_container_width=True): d['genre'] = g; add_msg("user", g); next_step("S1_DATE", "Release Date?")

        elif step == "S1_DATE":
            if st.button("ASAP"): d['date'] = "ASAP"; add_msg("user", "ASAP"); next_step("S1_UPC", "UPC?")
            
        elif step == "S1_UPC":
            if st.button("Generate Free"): d['upc'] = "AUTO"; add_msg("user", "Free UPC"); next_step("S1_LABEL", "Label Name?")
            st.chat_input("UPC...", key="i", on_submit=lambda: (d.update({"upc": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S1_LABEL", "Label Name?")))

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
            for i in ["Vocals", "Guitar", "Keys"]:
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
                    # FIX: LOGIC WAS LOOPING TO GENRE, NOW GOES TO LANG
                    next_step("S2_LANG", "Select **Lyrics Language**:") 
                    st.rerun()

        # --- RESTORED LYRICS LOGIC ---
        elif step == "S2_LANG":
            if st.button("English"): d['lang'] = "English"; add_msg("user", "English"); next_step("S2_EXPL", "Is it **Explicit**?")
            if st.button("Instrumental"): d['lang'] = "Instrumental"; add_msg("user", "Instrumental"); next_step("S2_ISRC", "ISRC?")

        elif step == "S2_EXPL":
            if st.button("Clean"): d['explicit'] = "Clean"; add_msg("user", "Clean"); next_step("S2_ISRC", "ISRC?")
            if st.button("Explicit"): d['explicit'] = "Explicit"; add_msg("user", "Explicit"); next_step("S2_ISRC", "ISRC?")

        elif step == "S2_ISRC":
            if st.button("Generate Free"): d['isrc'] = "AUTO"; add_msg("user", "Free ISRC"); next_step("S3_COVER", "Upload **Cover Art**")
            st.chat_input("ISRC...", key="i", on_submit=lambda: (d.update({"isrc": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S3_COVER", "Upload **Cover Art**")))

        # --- FILES ---
        elif step == "S3_COVER":
            f = st.file_uploader("Cover Art", type=["jpg", "png"])
            if f:
                d['cover'] = f; add_msg("user", "Uploaded Art")
                safe, reason = check_cover()
                next_step("S3_AUDIO", f"✅ {reason}\n\nUpload **Audio**.")
                st.rerun()

        elif step == "S3_AUDIO":
            f = st.file_uploader("Audio", type=["wav", "mp3"])
            if f:
                d['audio'] = f; add_msg("user", "Uploaded Audio")
                safe, reason = check_audio()
                if d['lang'] == "Instrumental":
                    next_step("REVIEW", f"✅ {reason}\n\nReview Release.")
                else:
                    next_step("S3_LYRICS", f"✅ {reason}\n\nTranscribing Lyrics...")
                st.rerun()

        elif step == "S3_LYRICS":
            txt = check_lyrics()
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
