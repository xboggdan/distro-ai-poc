import streamlit as st
import time
import os

# --- IMPORTS FOR AI CLIENTS ---
# We wrap these in try-except to prevent crashing if libraries aren't installed
try:
    from groq import Groq
    import google.generativeai as genai
    from openai import OpenAI
except ImportError:
    st.error("⚠️ Missing AI libraries. Please run: pip install groq google-generativeai openai")

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="BandLab DistroBot AI", page_icon="🔥", layout="wide")

st.markdown("""
<style>
    /* BANDLAB THEME */
    .stApp { background-color: #ffffff; color: #222; }
    
    /* Chat Bubbles */
    .stChatMessage {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
    }
    
    /* AI Source Badges */
    .model-badge {
        font-size: 0.7em;
        padding: 3px 8px;
        border-radius: 12px;
        font-weight: bold;
        display: inline-block;
        margin-top: 8px;
        font-family: 'Source Code Pro', monospace;
        letter-spacing: 0.5px;
    }
    
    /* Specific Model Colors */
    .badge-groq { background: #ffecb3; color: #ff6f00; border: 1px solid #ffca28; } /* Amber */
    .badge-gemini { background: #e3f2fd; color: #0277bd; border: 1px solid #81d4fa; } /* Blue */
    .badge-gpt { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; } /* Green */
    .badge-fallback { background: #f5f5f5; color: #616161; border: 1px solid #e0e0e0; } /* Grey */

    /* BandLab Red Button */
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
    
    /* Education Box */
    .edu-alert {
        background-color: #FFFDE7;
        border-left: 5px solid #FBC02D;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 15px;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. THE AI CASCADE ENGINE ---

def get_ai_response(prompt, context="general"):
    """
    Tries AI models in order: Groq -> Gemini -> GPT -> Fallback.
    Returns: (text_response, model_name, badge_class)
    """
    
    system_prompt = """
    You are DistroBot, a senior Music Distribution Expert at BandLab.
    Your goal is to help artists release music to Spotify/Apple Music correctly.
    
    RULES:
    1. Be concise, professional, and encouraging.
    2. Strictly follow DSP metadata style guides (No 'feat' in titles, strict cover art rules).
    3. If asked about BandLab specific features, mention that we keep 100% royalties.
    4. Provide educational context when the user is confused.
    """

    # 1. TRY GROQ (Speed Layer)
    if "GROQ_API_KEY" in st.secrets:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                model="llama3-70b-8192",
            )
            return chat_completion.choices[0].message.content, "Groq (Llama 3)", "badge-groq"
        except Exception as e:
            print(f"Groq Failed: {e}")
    
    # 2. TRY GEMINI (Balanced Layer)
    if "GEMINI_API_KEY" in st.secrets:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(system_prompt + "\n\nUser: " + prompt)
            return response.text, "Google Gemini", "badge-gemini"
        except Exception as e:
            print(f"Gemini Failed: {e}")

    # 3. TRY OPENAI (Reliability Layer)
    if "OPENAI_API_KEY" in st.secrets:
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content, "OpenAI GPT-4o", "badge-gpt"
        except Exception as e:
            print(f"OpenAI Failed: {e}")

    # 4. FALLBACK
    return "I am currently offline (API Keys missing or errors).", "Offline Fallback", "badge-fallback"

# --- 3. MOCK ANALYZERS (Still simulated for file I/O reasons) ---

def analyze_cover_art():
    with st.spinner("👁️ AI Vision Agent scanning for guidelines..."):
        time.sleep(2)
    return True, "Safe: No text or nudity detected."

def analyze_audio():
    with st.spinner("🎧 ACR Cloud scanning 80M+ database..."):
        time.sleep(2.5)
    return True, "Clean: No copyright strikes found."

def analyze_lyrics_whisper():
    with st.spinner("📝 Whisper AI transcribing audio..."):
        time.sleep(3)
    return """(Verse 1)
BandLab on the track, we moving fast
Distribution seamless, built to last
AI checking flows, checking the art
We getting ready for the charts

(Chorus)
Upload it now, to the world we go
Spotify, Apple, let the people know
"""

# --- 4. STATE MANAGEMENT ---

def init_state():
    if "step" not in st.session_state:
        st.session_state.update({
            "history": [],
            "edu_chat_history": [{"role": "assistant", "content": "🎓 **Education Mode Active**\n\nI'm connected to Groq, Gemini, and GPT. Ask me anything about music distribution!", "model": "System", "badge": "badge-fallback"}],
            "step": "INTRO",
            "edu_mode": False,
            "edit_return_mode": False,
            "temp_name": "",
            "transcribed_lyrics": "",
            "data": {
                "main_artist": "xboggdan",
                "release_title": "", "version": "", "genre": "", "upc": "", "release_date": "ASAP", "label": "",
                "composers": [], "performers": [], "production": [], "lyricists": [],
                "lyrics_lang": "English", "explicit": "Clean", "isrc": "", "audio": None, "cover": None, "final_lyrics": ""
            }
        })

init_state()

# --- 5. LOGIC & ROUTING ---

def add_msg(role, text, model_name="System", badge_class="badge-fallback"):
    msg = {
        "role": role, 
        "content": text, 
        "model": model_name, 
        "badge": badge_class
    }
    
    if st.session_state.edu_mode:
        st.session_state.edu_chat_history.append(msg)
    else:
        st.session_state.history.append(msg)

def next_step(step_id, prompt):
    if st.session_state.edit_return_mode:
        st.session_state.edit_return_mode = False
        st.session_state.step = "REVIEW"
        add_msg("assistant", "✅ Updated. Returning to Review.", "System", "badge-fallback")
    else:
        st.session_state.step = step_id
        add_msg("assistant", prompt, "System", "badge-fallback")

def start_wizard():
    st.session_state.step = "S1_TITLE"
    st.session_state.history = []
    add_msg("assistant", "🔥 **Let's Build Your Release.**\n\nI've detected your profile: **xboggdan**.\n\n**Step 1:** What is the **Release Title**?", "System", "badge-fallback")

# --- SMART ADDER LOGIC ---
def smart_add(role_type, is_me):
    d = st.session_state.data
    
    if is_me:
        add_msg("user", f"Yes, I am the {role_type[:-1]}")
        if role_type == "Composers":
            d['composers'].append(d['main_artist'])
            next_step("S2_COMPOSERS_MORE", f"Added **{d['main_artist']}**. Add another?")
        elif role_type == "Performers":
            st.session_state.temp_name = d['main_artist']
            next_step("S2_PERF_ROLE", f"What instrument did **{d['main_artist']}** play?")
        elif role_type == "Producers":
            st.session_state.temp_name = d['main_artist']
            next_step("S2_PROD_ROLE", f"What is **{d['main_artist']}**'s role?")
    else:
        add_msg("user", "Someone Else")
        if role_type == "Composers": next_step("S2_COMPOSERS_INPUT", "Enter **Legal First & Last Name**:")
        elif role_type == "Performers": next_step("S2_PERF_NAME", "Enter Performer Name:")
        elif role_type == "Producers": next_step("S2_PROD_NAME", "Enter Producer Name:")

# --- 6. UI RENDERERS ---

def render_sidebar():
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/BandLab_Technologies_logo.svg/2560px-BandLab_Technologies_logo.svg.png", width=160)
        
        st.markdown("### 🧠 Neural Core")
        st.caption("Active Models:")
        if "GROQ_API_KEY" in st.secrets: st.markdown("🟢 **Groq** (Llama 3)")
        if "GEMINI_API_KEY" in st.secrets: st.markdown("🔵 **Gemini** (Pro)")
        if "OPENAI_API_KEY" in st.secrets: st.markdown("🟣 **OpenAI** (GPT-4)")
        
        st.divider()
        
        # Education Toggle
        mode = st.toggle("🎓 Education Mode", value=st.session_state.edu_mode)
        if mode != st.session_state.edu_mode:
            st.session_state.edu_mode = mode
            st.rerun()
            
        if st.session_state.edu_mode:
            st.info("Ask any question. The AI Cascade will answer.")
        else:
            d = st.session_state.data
            st.markdown("### 📀 Release Draft")
            if d['release_title']:
                st.write(f"**{d['release_title']}**")
                st.caption(f"{d['main_artist']}")
            else:
                st.caption("Empty")
        
        if st.button("Reset Session"):
            st.session_state.clear()
            st.rerun()

def render_chat_stream(history):
    for msg in history:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])
            if msg.get('model'):
                st.markdown(f"<span class='model-badge {msg['badge']}'>⚡ {msg['model']}</span>", unsafe_allow_html=True)

# --- 7. MAIN APP ---

render_sidebar()

# MODE A: EDUCATION CHATBOT (REAL AI)
if st.session_state.edu_mode:
    st.title("🎓 Distribution Knowledge Base")
    render_chat_stream(st.session_state.edu_chat_history)
    
    query = st.chat_input("Ask about Royalties, ISRC, Cover Art...")
    if query:
        # 1. Show user message
        add_msg("user", query)
        st.rerun()

    # Process response if last message was user (to avoid blocking UI)
    last_msg = st.session_state.edu_chat_history[-1]
    if last_msg['role'] == "user":
        with st.spinner("🤖 AI Cascade thinking..."):
            # CALL THE REAL AI
            resp_text, model_name, badge_cls = get_ai_response(last_msg['content'])
            add_msg("assistant", resp_text, model_name, badge_cls)
            st.rerun()

# MODE B: RELEASE WIZARD
else:
    st.title("BandLab Distribution AI")
    
    if st.session_state.step == "INTRO":
        st.markdown("""
        <div style="background:#f9f9f9; padding:20px; border-radius:10px; border:1px solid #eee;">
            <h3>🚀 AI Release Wizard</h3>
            <p>Welcome to the future of distribution. This tool uses:</p>
            <ul>
                <li><b>Llama 3 / GPT-4</b> for metadata validation.</li>
                <li><b>Vision AI</b> for cover art compliance.</li>
                <li><b>Whisper</b> for automatic lyrics.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Release", use_container_width=True):
            start_wizard()
            st.rerun()
    
    else:
        render_chat_stream(st.session_state.history)
        
        step = st.session_state.step
        d = st.session_state.data

        # --- DYNAMIC INPUTS ---

        # 1. SIMPLE TEXT
        if step == "S1_TITLE":
            st.chat_input("Enter Title...", key="i", on_submit=lambda: (d.update({"release_title": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S1_VERSION", "Any specific **Version**?")))

        elif step == "S1_VERSION":
            if st.button("Skip / Original", use_container_width=True):
                add_msg("user", "Original")
                next_step("S1_GENRE", "Select **Genre**:")
                st.rerun()
            st.chat_input("e.g. Radio Edit...", key="i", on_submit=lambda: (d.update({"version": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S1_GENRE", "Select **Genre**:")))

        elif step == "S1_UPC":
            if st.button("Generate Free UPC", use_container_width=True):
                d['upc'] = "AUTO-GENERATED"
                add_msg("user", "Generate Free UPC")
                next_step("S1_LABEL", "**Record Label** name?")
                st.rerun()
            st.chat_input("Enter UPC...", key="i", on_submit=lambda: (d.update({"upc": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S1_LABEL", "**Record Label** name?")))

        elif step == "S1_LABEL":
            if st.button("Use Artist Name", use_container_width=True):
                d['label'] = d['main_artist']
                add_msg("user", d['main_artist'])
                next_step("S2_COMPOSERS_START", f"Is **{d['main_artist']}** the composer?")
                st.rerun()
            st.chat_input("Label Name...", key="i", on_submit=lambda: (d.update({"label": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S2_COMPOSERS_START", f"Is **{d['main_artist']}** the composer?")))

        # 2. SMART ROLES
        elif step == "S2_COMPOSERS_START":
            c1, c2 = st.columns(2)
            if c1.button(f"Yes, {d['main_artist']}", use_container_width=True): smart_add("Composers", True); st.rerun()
            if c2.button("No / Someone Else", use_container_width=True): smart_add("Composers", False); st.rerun()
            
        elif step == "S2_COMPOSERS_INPUT":
            st.chat_input("Legal Name...", key="i", on_submit=lambda: (d['composers'].append(st.session_state.i), add_msg("user", st.session_state.i), next_step("S2_COMPOSERS_MORE", "Add another?")))
            
        elif step == "S2_COMPOSERS_MORE":
            c1, c2 = st.columns(2)
            if c1.button("Add Another", use_container_width=True): next_step("S2_COMPOSERS_INPUT", "Name:"); st.rerun()
            if c2.button("Done", use_container_width=True): next_step("S2_PERF_START", f"Did **{d['main_artist']}** perform?"); st.rerun()

        elif step == "S2_PERF_START":
            c1, c2 = st.columns(2)
            if c1.button("Yes", use_container_width=True): smart_add("Performers", True); st.rerun()
            if c2.button("No", use_container_width=True): smart_add("Performers", False); st.rerun()

        elif step == "S2_PERF_NAME":
            st.chat_input("Name...", key="i", on_submit=lambda: (setattr(st.session_state, 'temp_name', st.session_state.i), add_msg("user", st.session_state.i), next_step("S2_PERF_ROLE", "Instrument?")))

        elif step == "S2_PERF_ROLE":
            cols = st.columns(4)
            for i, inst in enumerate(["Vocals", "Guitar", "Bass", "Drums", "Keys", "Other"]):
                if cols[i%4 if i<4 else 0].button(inst, use_container_width=True):
                    d['performers'].append({"name": st.session_state.temp_name, "role": inst})
                    add_msg("user", inst)
                    next_step("S2_PERF_MORE", "Add another?")
                    st.rerun()
                    
        elif step == "S2_PERF_MORE":
            c1, c2 = st.columns(2)
            if c1.button("Add Another", use_container_width=True): next_step("S2_PERF_NAME", "Name:"); st.rerun()
            if c2.button("Done", use_container_width=True): next_step("S2_PROD_START", f"Is **{d['main_artist']}** the producer?"); st.rerun()

        elif step == "S2_PROD_START":
            c1, c2 = st.columns(2)
            if c1.button("Yes", use_container_width=True): smart_add("Producers", True); st.rerun()
            if c2.button("No", use_container_width=True): smart_add("Producers", False); st.rerun()
            
        elif step == "S2_PROD_NAME":
             st.chat_input("Name...", key="i", on_submit=lambda: (setattr(st.session_state, 'temp_name', st.session_state.i), add_msg("user", st.session_state.i), next_step("S2_PROD_ROLE", "Role?")))

        elif step == "S2_PROD_ROLE":
            for r in ["Producer", "Mixing Engineer", "Mastering Engineer"]:
                if st.button(r, use_container_width=True):
                    d['production'].append({"name": st.session_state.temp_name, "role": r})
                    add_msg("user", r)
                    next_step("S1_GENRE", "Select **Genre**:")
                    st.rerun()

        # 3. SELECTORS
        elif step == "S1_GENRE":
            for g in ["Pop", "Hip Hop", "Rock", "R&B", "Electronic"]:
                if st.button(g, use_container_width=True):
                    d['genre'] = g
                    add_msg("user", g)
                    next_step("S1_DATE", "**Release Date**?")
                    st.rerun()

        elif step == "S1_DATE":
            if st.button("ASAP", use_container_width=True):
                d['release_date'] = "ASAP"
                add_msg("user", "ASAP")
                next_step("S1_UPC", "Do you have a **UPC**?")
                st.rerun()

        elif step == "S2_ISRC":
            if st.button("Generate Free ISRC", use_container_width=True):
                d['isrc'] = "AUTO"
                add_msg("user", "Generate Free")
                next_step("S3_COVER", "Upload **Cover Art**.")
                st.rerun()
            st.chat_input("Enter ISRC...", key="i", on_submit=lambda: (d.update({"isrc": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S3_COVER", "Upload **Cover Art**.")))

        # 4. FILES & AI CHECKS
        elif step == "S3_COVER":
            f = st.file_uploader("Upload Cover", type=["jpg","png"])
            if f:
                d['cover'] = f
                add_msg("user", "Uploaded Art")
                safe, reason = analyze_cover_art() # Mocked
                if safe:
                    next_step("S2_AUDIO", f"✅ {reason}\n\nUpload **Audio**.", "Vision Agent", "badge-gemini")
                st.rerun()

        elif step == "S2_AUDIO":
            f = st.file_uploader("Upload Audio", type=["wav","mp3"])
            if f:
                d['audio'] = f
                add_msg("user", "Uploaded Audio")
                safe, reason = analyze_audio() # Mocked
                next_step("S2_LYRICS_TRANS", f"✅ {reason}\n\nGenerating Lyrics...", "Audio Agent", "badge-gemini")
                st.rerun()

        elif step == "S2_LYRICS_TRANS":
            lyrics = analyze_lyrics_whisper() # Mocked
            st.session_state.transcribed_lyrics = lyrics
            next_step("S2_LYRICS_EDIT", "📝 **Lyrics Generated.** Please verify.", "Lyrics Agent", "badge-groq")
            st.rerun()

        elif step == "S2_LYRICS_EDIT":
            val = st.text_area("Editor", value=st.session_state.transcribed_lyrics, height=200)
            if st.button("Confirm Lyrics", use_container_width=True):
                d['final_lyrics'] = val
                add_msg("user", "Lyrics Confirmed")
                next_step("REVIEW", "🎉 Release Data Complete!")
                st.rerun()

        # 5. REVIEW
        elif step == "REVIEW":
            st.subheader("💿 Summary")
            st.write(f"**Title:** {d['release_title']}")
            st.write(f"**UPC:** {d['upc']}")
            st.write(f"**Producers:** {len(d['production'])}")
            
            if st.button("🚀 SUBMIT", use_container_width=True):
                st.balloons()
                st.success("Sent to Distribution!")
