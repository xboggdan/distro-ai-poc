import streamlit as st
import openai
import google.generativeai as genai
import json
import re
import time
import random
from datetime import date, timedelta, datetime

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="DistroBot V8", layout="centered", page_icon="💿")

st.markdown("""
    <style>
        .stButton > button {
            border-radius: 20px;
            border: 1px solid #E0E0E0;
            background-color: #ffffff;
            color: #31333F;
            padding: 5px 15px;
            font-size: 14px;
            margin-right: 5px;
            transition: all 0.3s;
        }
        .stButton > button:hover {
            border-color: #FF4B4B;
            color: #FF4B4B;
            background-color: #FFF5F5;
        }
        .info-box {
            background-color: #e8f4f8;
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #00a8e8;
            margin-bottom: 20px;
            font-size: 14px;
        }
        .ai-fix-box {
            background-color: #f3e5f5;
            padding: 15px;
            border-radius: 10px;
            border: 1px dashed #9c27b0;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# Retrieve Keys
openai_key = st.secrets.get("OPENAI_API_KEY")
gemini_key = st.secrets.get("GEMINI_API_KEY")
groq_key = st.secrets.get("GROQ_API_KEY")

if gemini_key:
    genai.configure(api_key=gemini_key)

# --- 2. HOW IT WORKS ---
with st.expander("📚 READ ME: V8 Capabilities & Testing", expanded=False):
    st.markdown("""
    ### 🚀 New V8 Features
    1.  **AI Art Fixer:** Upload any image. The bot will simulate finding a text mismatch and offer a "Magic Fix" button.
    2.  **Date Guardrails:** Try selecting a date tomorrow. It will block you (Must be 14-90 days out).
    3.  **Inheritance:** Watch how it **skips** Track Title but tells you it copied the Release Title.
    4.  **Conditional Logic:** Select "Instrumental" -> It skips Explicit/Lyricist questions.
    """)

# --- 3. KNOWLEDGE BASE ---
DISTRO_KNOWLEDGE_BASE = """
VALIDATION RULES (STRICT):
1. Release Title: FORBIDDEN: 'feat', 'prod', 'remix', emojis. Brackets () allowed.
2. Version: FORBIDDEN: 'Original', 'Official', 'Explicit'. ALLOWED: 'Remix', 'Acoustic'.
3. Artist Name: FORBIDDEN: 'feat', 'prod' inside name.
4. Composer: MUST BE Legal First & Last Name.
5. Date: Must be between 14 days and 3 months from today.
"""

# --- 4. ROBUST AI ENGINE ---

def clean_json(raw_text):
    try:
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match: return json.loads(match.group(0))
        return json.loads(raw_text)
    except: return None

def query_ai_engine(user_input, current_field, context_str=""):
    """
    Validates text inputs against the Knowledge Base.
    """
    system_prompt = f"""
    You are DistroBot QC.
    RULES: {DISTRO_KNOWLEDGE_BASE}
    
    CONTEXT: Field="{current_field}". {context_str}
    INPUT: "{user_input}"
    
    INSTRUCTIONS:
    1. FAQ CHECK: If user asks a question, return type="question".
    2. SKIP CHECK: If input is "none", "skip", "no", return type="skip".
    3. VALIDATE: Check against rules.
    
    RETURN JSON ONLY: {{ "valid": true }} OR {{ "valid": false, "error": "Reason" }} OR {{ "type": "question", "reply": "..." }}
    """
    
    try:
        if groq_key:
            client = openai.OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": system_prompt}],
                response_format={"type": "json_object"},
                temperature=0
            )
            return clean_json(resp.choices[0].message.content)
    except:
        return {"valid": True} # Fail open

# --- 5. APP LOGIC & STATE ---

if "messages" not in st.session_state:
    st.session_state.messages = []
if "step_id" not in st.session_state:
    st.session_state.step_id = "start"
if "data" not in st.session_state:
    st.session_state.data = {}
if "art_fixed" not in st.session_state:
    st.session_state.art_fixed = False

def bot_say(text):
    with st.chat_message("assistant"):
        st.markdown(text)

def add_user_msg(text):
    st.session_state.messages.append({"role": "user", "content": str(text)})

def next_step(target_id):
    st.session_state.step_id = target_id
    st.rerun()

# --- 6. WORKFLOW STEPS (THE STATE MACHINE) ---

st.title("🤖 DistroBot V8")

# History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- STEP: START ---
if st.session_state.step_id == "start":
    bot_say("👋 Hi! I'm DistroBot. I'll guide you through your release.\n\n**First, what is the Title of your Release?**")
    st.session_state.step_id = "release_title"

# --- STEP: RELEASE TITLE ---
elif st.session_state.step_id == "release_title":
    val = st.chat_input("Release Title...")
    if val:
        add_user_msg(val)
        res = query_ai_engine(val, "Release Title")
        if res.get("valid", True):
            st.session_state.data["release_title"] = val
            next_step("version")
        else:
            bot_say(f"🚫 {res['error']}")

# --- STEP: VERSION ---
elif st.session_state.step_id == "version":
    bot_say("Is there a specific **Version**? (e.g., Remix). Click 'Skip' for Original.")
    col1, col2 = st.columns(2)
    if col1.button("Skip / Original"):
        add_user_msg("Skip")
        st.session_state.data["version"] = ""
        next_step("artist")
    
    val = st.chat_input("Version...")
    if val:
        add_user_msg(val)
        res = query_ai_engine(val, "Version")
        if res.get("valid", True):
            st.session_state.data["version"] = val
            next_step("artist")
        else:
            bot_say(f"🚫 {res['error']}")

# --- STEP: ARTIST ---
elif st.session_state.step_id == "artist":
    bot_say("**Primary Artist Name?**")
    val = st.chat_input("Artist Name...")
    if val:
        add_user_msg(val)
        res = query_ai_engine(val, "Artist Name")
        if res.get("valid", True):
            st.session_state.data["artist"] = val
            next_step("genre")
        else:
            bot_say(f"🚫 {res['error']}")

# --- STEP: GENRE ---
elif st.session_state.step_id == "genre":
    bot_say("Select your **Genre**:")
    genres = ["Pop", "Hip-Hop", "Rock", "Electronic", "R&B", "Latin"]
    cols = st.columns(3)
    for i, g in enumerate(genres):
        if cols[i%3].button(g):
            add_user_msg(g)
            st.session_state.data["genre"] = g
            next_step("upc_label_ask")

# --- STEP: UPC/LABEL ASK ---
elif st.session_state.step_id == "upc_label_ask":
    bot_say("Do you want to add a custom **UPC** or **Label Name**?")
    c1, c2 = st.columns(2)
    if c1.button("Yes, add details"):
        add_user_msg("Yes")
        next_step("label_input")
    if c2.button("No, skip"):
        add_user_msg("No")
        st.session_state.data["label"] = ""
        st.session_state.data["upc"] = ""
        next_step("date_ask")

# --- STEP: LABEL INPUT ---
elif st.session_state.step_id == "label_input":
    bot_say("Enter **Label Name** (or type 'Skip'):")
    val = st.chat_input("Label...")
    if val:
        add_user_msg(val)
        st.session_state.data["label"] = val if val.lower() != "skip" else ""
        next_step("date_ask")

# --- STEP: DATE SELECTION ---
elif st.session_state.step_id == "date_ask":
    bot_say("When should this go live?")
    c1, c2 = st.columns(2)
    if c1.button("As Soon As Possible"):
        add_user_msg("ASAP")
        st.session_state.data["date"] = "ASAP"
        next_step("cover_art")
    if c2.button("Specific Date"):
        add_user_msg("Specific Date")
        next_step("date_input")

# --- STEP: DATE INPUT (LOGIC) ---
elif st.session_state.step_id == "date_input":
    bot_say("Please enter format YYYY-MM-DD. **Must be 14 days to 3 months from today.**")
    val = st.chat_input("YYYY-MM-DD")
    if val:
        add_user_msg(val)
        try:
            input_date = datetime.strptime(val, "%Y-%m-%d").date()
            today = date.today()
            min_date = today + timedelta(days=14)
            max_date = today + timedelta(days=90)
            
            if min_date <= input_date <= max_date:
                st.session_state.data["date"] = val
                next_step("cover_art")
            else:
                bot_say(f"🚫 Date must be between {min_date} and {max_date}.")
        except ValueError:
            bot_say("🚫 Invalid format. Use YYYY-MM-DD.")

# --- STEP: COVER ART (AI FIXER) ---
elif st.session_state.step_id == "cover_art":
    bot_say("🎨 **Upload Cover Art**.")
    up = st.file_uploader("Image", type=["jpg", "png"])
    
    if up:
        if not st.session_state.art_fixed:
            # SIMULATE AI ANALYSIS
            with st.spinner("🤖 Scanning image text..."):
                time.sleep(1.5)
            
            # SIMULATE ERROR FINDING
            st.markdown("""
            <div class='ai-fix-box'>
                <b>⚠️ AI Alert:</b> I detected text on the cover that doesn't match your Artist Name ("Bogdan").<br>
                This will get rejected by Spotify.
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("✨ Fix with Nano Banana AI"):
                with st.spinner("🍌 Nano Banana is removing text..."):
                    time.sleep(2)
                st.session_state.art_fixed = True
                st.success("Text removed! Image is now compliant.")
                st.rerun()
        else:
            bot_say("✅ Fixed image confirmed.")
            if st.button("Next Step"):
                st.session_state.data["artwork"] = "Fixed_Image.jpg"
                next_step("track_logic")

# --- STEP: TRACK LOGIC (INHERITANCE) ---
elif st.session_state.step_id == "track_logic":
    # Since this is a single flow demo, we auto-inherit
    st.session_state.data["track_title"] = st.session_state.data["release_title"]
    st.session_state.data["track_version"] = st.session_state.data["version"]
    
    bot_say(f"ℹ️ **Single Track Mode:** I've automatically set the Track Title to **'{st.session_state.data['release_title']}'** to match the release.")
    time.sleep(1.5)
    next_step("prev_released")

# --- STEP: PREVIOUSLY RELEASED ---
elif st.session_state.step_id == "prev_released":
    bot_say("Has this track been released before?")
    c1, c2 = st.columns(2)
    if c1.button("Yes"):
        add_user_msg("Yes")
        st.session_state.data["prev_released"] = True
        next_step("audio_upload")
    if c2.button("No"):
        add_user_msg("No")
        st.session_state.data["prev_released"] = False
        next_step("audio_upload")

# --- STEP: AUDIO UPLOAD ---
elif st.session_state.step_id == "audio_upload":
    bot_say("Upload Audio (WAV/FLAC).")
    up = st.file_uploader("Audio", type=["wav", "mp3"])
    if up:
        st.session_state.data["audio"] = up.name
        if st.button("Confirm Audio"):
            next_step("language")

# --- STEP: LANGUAGE ---
elif st.session_state.step_id == "language":
    bot_say("What **Language** are the lyrics in?")
    opts = ["English", "Spanish", "Instrumental (No Lyrics)"]
    cols = st.columns(3)
    for i, o in enumerate(opts):
        if cols[i].button(o):
            add_user_msg(o)
            st.session_state.data["language"] = o
            if "Instrumental" in o:
                # SKIP Explicit & Lyricist
                st.session_state.data["explicit"] = "Clean"
                st.session_state.data["lyricist"] = "N/A"
                next_step("credits_performer")
            else:
                next_step("explicit")

# --- STEP: EXPLICIT ---
elif st.session_state.step_id == "explicit":
    bot_say("Is the content **Explicit**?")
    c1, c2 = st.columns(2)
    if c1.button("Clean"):
        add_user_msg("Clean")
        st.session_state.data["explicit"] = "Clean"
        next_step("lyricist_ask")
    if c2.button("Explicit"):
        add_user_msg("Explicit")
        st.session_state.data["explicit"] = "Explicit"
        next_step("lyricist_ask")

# --- STEP: LYRICIST ---
elif st.session_state.step_id == "lyricist_ask":
    bot_say("Are you the **Lyricist**?")
    c1, c2 = st.columns(2)
    if c1.button("Yes"):
        add_user_msg("Yes")
        # Assuming Artist Name is real name for demo, or ask legal name
        st.session_state.data["lyricist"] = st.session_state.data["artist"] 
        next_step("credits_performer")
    if c2.button("No (Enter Name)"):
        add_user_msg("No")
        next_step("lyricist_input")

elif st.session_state.step_id == "lyricist_input":
    val = st.chat_input("Lyricist Legal Name")
    if val:
        add_user_msg(val)
        st.session_state.data["lyricist"] = val
        next_step("credits_performer")

# --- STEP: PERFORMER CREDITS ---
elif st.session_state.step_id == "credits_performer":
    bot_say("Are you the main **Performer**?")
    c1, c2 = st.columns(2)
    if c1.button("Yes"):
        add_user_msg("Yes")
        st.session_state.data["performer"] = st.session_state.data["artist"]
        next_step("performer_inst")
    if c2.button("Someone else"):
        add_user_msg("Someone else")
        next_step("performer_input")

elif st.session_state.step_id == "performer_inst":
    bot_say("Select **Instrument**:")
    insts = ["Vocals", "Guitar", "Drums", "Synth"]
    cols = st.columns(4)
    for i, inst in enumerate(insts):
        if cols[i].button(inst):
            add_user_msg(inst)
            st.session_state.data["instrument"] = inst
            next_step("credits_prod")

# --- STEP: PRODUCER CREDITS ---
elif st.session_state.step_id == "credits_prod":
    bot_say("Select **Production Role**:")
    roles = ["Producer", "Mixing Engineer", "Mastering Engineer"]
    cols = st.columns(3)
    for i, r in enumerate(roles):
        if cols[i].button(r):
            add_user_msg(r)
            st.session_state.data["prod_role"] = r
            next_step("contributors")

# --- STEP: CONTRIBUTORS ---
elif st.session_state.step_id == "contributors":
    bot_say("Do you have any **Contributors** (feat. artists)?")
    c1, c2 = st.columns(2)
    if c1.button("Yes"):
        add_user_msg("Yes")
        next_step("contrib_input")
    if c2.button("No"):
        add_user_msg("No")
        next_step("optional_ids")

elif st.session_state.step_id == "contrib_input":
    bot_say("Enter **Contributor Name**:")
    val = st.chat_input("Name...")
    if val:
        add_user_msg(val)
        st.session_state.data["contributor"] = val
        next_step("optional_ids")

# --- STEP: OPTIONAL IDS (ISRC/PUB) ---
elif st.session_state.step_id == "optional_ids":
    bot_say("Add **ISRC** or **Publisher**? (Optional)")
    c1, c2 = st.columns(2)
    if c1.button("Skip All"):
        add_user_msg("Skip")
        next_step("summary")
    if c2.button("Enter Details"):
        add_user_msg("Enter Details")
        next_step("isrc_input")

elif st.session_state.step_id == "isrc_input":
    val = st.chat_input("Enter ISRC or type Skip")
    if val:
        add_user_msg(val)
        st.session_state.data["isrc"] = val
        next_step("summary")

# --- STEP: SUMMARY ---
elif st.session_state.step_id == "summary":
    bot_say("✅ **Release Ready!** Review details:")
    st.json(st.session_state.data)
    if st.button("🚀 Submit Release"):
        st.balloons()
        st.success("Sent to QC!")
    if st.button("🔄 Restart"):
        st.session_state.clear()
        st.rerun()
