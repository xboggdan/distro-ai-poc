import streamlit as st
import time
import random

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="BandLab DistroBot AI", page_icon="🤖", layout="wide")

st.markdown("""
<style>
    /* BANDLAB BRANDING & UI POLISH */
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

    /* Secondary / Skip Button */
    .skip-btn { border: 1px solid #ccc; color: #555; background: white; }

    /* AI Analysis Badges */
    .ai-badge {
        font-size: 0.75em; padding: 4px 8px; border-radius: 6px;
        display: inline-block; margin-top: 5px; font-weight: bold; font-family: monospace;
    }
    .badge-vision { background: #E3F2FD; color: #1565C0; border: 1px solid #90CAF9; }
    .badge-audio { background: #E8F5E9; color: #2E7D32; border: 1px solid #A5D6A7; }
    .badge-lyrics { background: #F3E5F5; color: #7B1FA2; border: 1px solid #CE93D8; }

    /* Lyrics Editor Area */
    .stTextArea textarea {
        background-color: #fafafa;
        border: 1px solid #eee;
        font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. MOCK AI SERVICES ---

def mock_vision_analysis():
    """Simulates Groq/Llava checking cover art"""
    with st.spinner("👁️ AI Vision Agent checking for explicit content & text..."):
        time.sleep(2.0)
    return True, "Safe: No nudity or illegal text detected."

def mock_acr_cloud_scan():
    """Simulates ACR Cloud copyright check"""
    with st.spinner("🎧 ACR Cloud scanning 80M+ tracks for copyright..."):
        time.sleep(2.5)
    return True, "Clean: No copyright matches found."

def mock_whisper_transcribe():
    """Simulates Whisper AI generating lyrics"""
    with st.spinner("📝 Whisper AI transcribing lyrics..."):
        time.sleep(3.0)
    return """(Verse 1)
Yeah, we rolling down the street
BandLab on the beat
Distribution made easy, you see
Just chatting with the AI, feeling free

(Chorus)
Upload, release, let it fly
To Spotify and Apple, reaching for the sky
No more forms, no more stress
DistroBot is here to handle the rest
"""

def mock_edu_bot_response(query):
    """Simulates the Education Chatbot RAG response"""
    time.sleep(1) # Thinking time
    query = query.lower()
    if "royalties" in query:
        return "💰 **Royalties:** You keep 100% of your royalties with BandLab Distribution. Payouts are processed monthly once stores report their earnings."
    elif "upc" in query:
        return "🏷️ **UPC (Universal Product Code):** This is the barcode for your album/single. If you don't have one, we assign a unique one to you for free."
    elif "isrc" in query:
        return "🎵 **ISRC:** This code identifies a specific recording (the audio file). It ensures you get paid even if your song appears on a compilation album."
    elif "cover" in query:
        return "🖼️ **Cover Art:** Must be 3000x3000px JPG/PNG. No blurred images, no pricing info, and no URLs allowed."
    else:
        return "🤖 I can help with questions about Royalties, UPCs, ISRCs, Cover Art, or Release Dates. What would you like to know?"

# --- 3. STATE MANAGEMENT ---

def init_state():
    defaults = {
        "history": [],
        "edu_history": [{"role": "assistant", "content": "🎓 **Education Mode Active**\n\nI am paused on your release. Ask me anything about music distribution, royalties, or metadata!"}],
        "step": "INTRO", 
        "edu_mode": False,
        "edit_return_mode": False,
        
        # Temp holders
        "temp_name": "",
        "transcribed_lyrics": "",
        
        # Release Data
        "data": {
            "main_artist": "xboggdan",
            "release_title": "", "version": "", "genre": "", "upc": "", "release_date": "ASAP", "label": "",
            "composers": [], "performers": [], "production": [], "lyricists": [],
            "lyrics_lang": "English", "explicit": "Clean", "isrc": "", "audio": None, "cover": None, "final_lyrics": ""
        }
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# --- 4. LOGIC HANDLERS ---

def add_msg(role, text, badge=None):
    msg = {"role": role, "content": text}
    if badge: msg["badge"] = badge
    
    if st.session_state.edu_mode:
        st.session_state.edu_history.append(msg)
    else:
        st.session_state.history.append(msg)

def next_step(step_id, bot_msg, badge=None):
    if st.session_state.edit_return_mode:
        st.session_state.edit_return_mode = False
        st.session_state.step = "REVIEW"
        add_msg("assistant", "✅ Updated. Returning to Review.")
    else:
        st.session_state.step = step_id
        add_msg("assistant", bot_msg, badge)

def start_chat():
    st.session_state.step = "S1_TITLE"
    st.session_state.history = [] # Clear intro
    add_msg("assistant", "🔥 **Let's get started.**\n\nI'll guide you step-by-step. I've detected your Main Artist profile is **xboggdan**.\n\n**Step 1:** What is the **Release Title**?")

# --- SMART ADDERS (Composers, Performers, Producers) ---

def smart_add_person(role_type, is_me):
    d = st.session_state.data
    name = d['main_artist'] if is_me else "Someone Else"
    
    if is_me:
        add_msg("user", f"Yes, I am the {role_type[:-1]}")
        if role_type == "Composers":
            d['composers'].append(d['main_artist'])
            next_step("S2_COMPOSERS_MORE", f"Added **{d['main_artist']}**. Any others?")
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

# --- 5. UI COMPONENTS ---

def render_sidebar():
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/BandLab_Technologies_logo.svg/2560px-BandLab_Technologies_logo.svg.png", width=150)
        
        # MODE SWITCHER
        st.markdown("### 🧠 AI Modes")
        mode = st.toggle("🎓 Education Bot", value=st.session_state.edu_mode)
        
        if mode != st.session_state.edu_mode:
            st.session_state.edu_mode = mode
            st.rerun()

        if st.session_state.edu_mode:
            st.info("You are chatting with the **Knowledge Base**. Toggle off to resume release.")
        else:
            d = st.session_state.data
            st.markdown("### 📀 Live Draft")
            if d['release_title']:
                st.write(f"**{d['release_title']}**")
                st.caption(f"{d['main_artist']} • {d['genre']}")
            else:
                st.caption("No data yet.")

        if st.button("Reset All"):
            st.session_state.clear()
            st.rerun()

def render_chat_history(history):
    for msg in history:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])
            if "badge" in msg:
                b_cls = "badge-vision" if "Vision" in msg['badge'] else "badge-audio" if "Audio" in msg['badge'] else "badge-lyrics"
                st.markdown(f"<span class='ai-badge {b_cls}'>⚡ {msg['badge']}</span>", unsafe_allow_html=True)

# --- 6. MAIN APP LOGIC ---

render_sidebar()

# A. EDUCATION MODE (FULL BOT SWAP)
if st.session_state.edu_mode:
    st.title("🎓 Distribution Knowledge Base")
    render_chat_history(st.session_state.edu_history)
    
    user_q = st.chat_input("Ask about UPCs, Royalties, Cover Art...")
    if user_q:
        add_msg("user", user_q)
        response = mock_edu_bot_response(user_q)
        add_msg("assistant", response)
        st.rerun()

# B. RELEASE MODE (NORMAL FLOW)
else:
    st.title("BandLab Distribution AI")
    
    if st.session_state.step == "INTRO":
        st.markdown("""
        <div style="border:1px solid #ddd; padding:20px; border-radius:10px; text-align:center; background:#fafafa;">
            <h3>🤖 AI-Powered Release Agent</h3>
            <p>I use 3 AI models to ensure your release is perfect:</p>
            <p>👁️ <b>Groq Vision:</b> Checks artwork compliance.<br>
            🎧 <b>ACR Cloud:</b> Checks copyright.<br>
            📝 <b>Whisper:</b> Transcribes lyrics automatically.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Start New Release", use_container_width=True):
            start_chat()
            st.rerun()
            
    else:
        render_chat_history(st.session_state.history)
        
        step = st.session_state.step
        d = st.session_state.data
        
        # --- INPUT ROUTER ---
        
        # 1. SIMPLE TEXT INPUTS
        if step == "S1_TITLE":
            st.chat_input("Track Title...", key="i", on_submit=lambda: (d.update({"release_title": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S1_VERSION", "Any specific **Version**?")))
            
        elif step == "S1_VERSION":
            if st.button("Skip / Original Mix", use_container_width=True):
                add_msg("user", "Original Mix")
                next_step("S1_GENRE", "Select **Genre**:")
                st.rerun()
            st.chat_input("e.g. Radio Edit...", key="i", on_submit=lambda: (d.update({"version": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S1_GENRE", "Select **Genre**:")))

        elif step == "S1_UPC":
            if st.button("Generate Free UPC", use_container_width=True):
                d['upc'] = "AUTO-GENERATED"
                add_msg("user", "Generate Free UPC")
                next_step("S1_LABEL", "**Record Label** name?")
                st.rerun()
            st.chat_input("Enter 12-digit UPC...", key="i", on_submit=lambda: (d.update({"upc": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S1_LABEL", "**Record Label** name?")))

        elif step == "S1_LABEL":
            if st.button("Skip / Use Artist Name", use_container_width=True):
                d['label'] = d['main_artist']
                add_msg("user", "Use Artist Name")
                next_step("S2_COMPOSERS_START", f"**Composers:** Is **{d['main_artist']}** the composer?")
                st.rerun()
            st.chat_input("Label Name...", key="i", on_submit=lambda: (d.update({"label": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S2_COMPOSERS_START", f"Is **{d['main_artist']}** the composer?")))

        # 2. SMART ROLES (Composers, Performers, Producers)
        elif step == "S2_COMPOSERS_START":
            c1, c2 = st.columns(2)
            if c1.button(f"Yes, {d['main_artist']}", use_container_width=True): smart_add_person("Composers", True); st.rerun()
            if c2.button("No / Someone Else", use_container_width=True): smart_add_person("Composers", False); st.rerun()

        elif step == "S2_COMPOSERS_INPUT":
            st.chat_input("Legal First & Last Name...", key="i", on_submit=lambda: (d['composers'].append(st.session_state.i), add_msg("user", st.session_state.i), next_step("S2_COMPOSERS_MORE", f"Added {st.session_state.i}. Any others?")))

        elif step == "S2_COMPOSERS_MORE":
            c1, c2 = st.columns(2)
            if c1.button("Add Another", use_container_width=True): next_step("S2_COMPOSERS_INPUT", "Enter Name:"); st.rerun()
            if c2.button("Done", use_container_width=True): next_step("S2_PERF_START", f"**Performers:** Did **{d['main_artist']}** perform?"); st.rerun()

        elif step == "S2_PERF_START":
            c1, c2 = st.columns(2)
            if c1.button(f"Yes, {d['main_artist']}", use_container_width=True): smart_add_person("Performers", True); st.rerun()
            if c2.button("No / Someone Else", use_container_width=True): smart_add_person("Performers", False); st.rerun()

        elif step == "S2_PERF_NAME":
            st.chat_input("Performer Name...", key="i", on_submit=lambda: (setattr(st.session_state, 'temp_name', st.session_state.i), add_msg("user", st.session_state.i), next_step("S2_PERF_ROLE", f"Instrument for **{st.session_state.i}**?")))
        
        elif step == "S2_PERF_ROLE":
            cols = st.columns(4)
            insts = ["Vocals", "Guitar", "Bass", "Drums", "Keys", "Other"]
            for i, inst in enumerate(insts):
                if cols[i%4 if i<4 else 0].button(inst, use_container_width=True):
                    d['performers'].append({"name": st.session_state.temp_name, "role": inst})
                    add_msg("user", inst)
                    next_step("S2_PERF_MORE", "Add another performer?")
                    st.rerun()

        elif step == "S2_PERF_MORE":
            c1, c2 = st.columns(2)
            if c1.button("Add Another", use_container_width=True): next_step("S2_PERF_NAME", "Enter Name:"); st.rerun()
            if c2.button("Done", use_container_width=True): next_step("S2_PROD_START", f"**Production:** Is **{d['main_artist']}** the producer?"); st.rerun()

        # 3. PRODUCER LOGIC (NEW REQUEST)
        elif step == "S2_PROD_START":
            c1, c2 = st.columns(2)
            if c1.button(f"Yes, {d['main_artist']}", use_container_width=True): smart_add_person("Producers", True); st.rerun()
            if c2.button("No / Someone Else", use_container_width=True): smart_add_person("Producers", False); st.rerun()

        elif step == "S2_PROD_NAME":
             st.chat_input("Producer Name...", key="i", on_submit=lambda: (setattr(st.session_state, 'temp_name', st.session_state.i), add_msg("user", st.session_state.i), next_step("S2_PROD_ROLE", "Select Role:")))

        elif step == "S2_PROD_ROLE":
            roles = ["Producer", "Mixing Engineer", "Mastering Engineer"]
            for r in roles:
                if st.button(r, use_container_width=True):
                    d['production'].append({"name": st.session_state.temp_name, "role": r})
                    add_msg("user", r)
                    next_step("S2_LYRICS_LANG", "Select **Language**:")
                    st.rerun()

        # 4. LYRICS & ASSETS
        elif step == "S1_GENRE":
            genres = ["Pop", "Hip Hop", "Rock", "R&B", "Electronic"]
            for g in genres:
                if st.button(g, use_container_width=True):
                    d['genre'] = g
                    add_msg("user", g)
                    next_step("S1_DATE", "Release Date?")
                    st.rerun()
                    
        elif step == "S1_DATE":
            if st.button("ASAP", use_container_width=True):
                d['release_date'] = "ASAP"
                add_msg("user", "ASAP")
                next_step("S1_UPC", "Do you have a **UPC**?")
                st.rerun()
            
        elif step == "S2_LYRICS_LANG":
            if st.button("English", use_container_width=True):
                d['lyrics_lang'] = "English"
                add_msg("user", "English")
                next_step("S2_EXPLICIT", "Is it **Explicit**?")
                st.rerun()
            if st.button("Instrumental", use_container_width=True):
                d['lyrics_lang'] = "Instrumental"
                add_msg("user", "Instrumental")
                next_step("S2_ISRC", "Do you have an **ISRC**?")
                st.rerun()

        elif step == "S2_EXPLICIT":
            c1, c2 = st.columns(2)
            if c1.button("Clean", use_container_width=True): d['explicit']="Clean"; add_msg("user","Clean"); next_step("S2_ISRC","**ISRC**?"); st.rerun()
            if c2.button("Explicit", use_container_width=True): d['explicit']="Explicit"; add_msg("user","Explicit"); next_step("S2_ISRC","**ISRC**?"); st.rerun()

        elif step == "S2_ISRC":
            if st.button("Generate Free ISRC", use_container_width=True):
                d['isrc'] = "AUTO-GENERATED"
                add_msg("user", "Generate Free ISRC")
                next_step("S3_COVER", "Upload **Cover Art**.")
                st.rerun()
            st.chat_input("Enter ISRC...", key="i", on_submit=lambda: (d.update({"isrc": st.session_state.i}), add_msg("user", st.session_state.i), next_step("S3_COVER", "Upload **Cover Art**.")))

        # 5. AI CHECKS (VISION, AUDIO, LYRICS)
        elif step == "S3_COVER":
            f = st.file_uploader("JPG/PNG 3000px", type=["jpg","png"])
            if f:
                d['cover'] = f
                add_msg("user", "🖼️ Art Uploaded")
                
                # MOCK VISION CHECK
                is_safe, reason = mock_vision_analysis()
                if is_safe:
                    next_step("S2_AUDIO", f"✅ {reason}\n\nNow upload **Audio File**.", "Vision Agent")
                else:
                    st.error("Issues detected with artwork.")
                st.rerun()

        elif step == "S2_AUDIO":
            f = st.file_uploader("WAV/MP3", type=["wav","mp3"])
            if f:
                d['audio'] = f
                add_msg("user", "🎵 Audio Uploaded")
                
                # MOCK AUDIO CHECK
                is_clean, reason = mock_acr_cloud_scan()
                if is_clean:
                    if d['lyrics_lang'] == "Instrumental":
                        next_step("REVIEW", f"✅ {reason}\n\nReview your release.", "Audio Agent")
                    else:
                        next_step("S2_LYRICS_TRANS", f"✅ {reason}\n\nTranscribing Lyrics...", "Audio Agent")
                st.rerun()

        elif step == "S2_LYRICS_TRANS":
            # MOCK WHISPER CHECK
            lyrics = mock_whisper_transcribe()
            st.session_state.transcribed_lyrics = lyrics
            next_step("S2_LYRICS_EDIT", "📝 **Lyrics Generated.** Please review and edit before sending to DSPs.", "Lyrics Agent")
            st.rerun()

        elif step == "S2_LYRICS_EDIT":
            edited_lyrics = st.text_area("Edit Lyrics", value=st.session_state.transcribed_lyrics, height=200)
            st.warning("These lyrics will be sent to Spotify/Apple. Ensure accuracy.")
            
            if st.button("✅ Confirm Lyrics", use_container_width=True):
                d['final_lyrics'] = edited_lyrics
                add_msg("user", "Lyrics Confirmed")
                next_step("REVIEW", "🎉 Release Data Complete!")
                st.rerun()

        # 6. FINAL REVIEW
        elif step == "REVIEW":
            st.subheader("💿 Release Summary")
            st.caption("Click Edit to modify specific fields.")
            
            def row(label, val, edit_step):
                c1, c2 = st.columns([4,1])
                c1.markdown(f"**{label}:** {val}")
                if c2.button("Edit", key=label):
                    st.session_state.edit_return_mode = True
                    st.session_state.step = edit_step
                    add_msg("assistant", f"Enter new **{label}**:")
                    st.rerun()

            row("Title", d['release_title'], "S1_TITLE")
            row("UPC", d['upc'], "S1_UPC")
            row("Explicit", d['explicit'], "S2_EXPLICIT")
            
            st.divider()
            st.write(f"**Composers:** {', '.join(d['composers'])}")
            st.write(f"**Performers:** {len(d['performers'])}")
            st.write(f"**Producers:** {len(d['production'])}")
            
            if d['lyrics_lang'] != "Instrumental":
                with st.expander("View Final Lyrics"):
                    st.text(d['final_lyrics'])
            
            if st.button("🚀 SUBMIT TO STORES", use_container_width=True):
                st.balloons()
                st.success("Release Submitted! Agents are monitoring delivery.")
