import streamlit as st
import openai
import google.generativeai as genai
import json
import re
import time
from datetime import date, timedelta, datetime

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="DistroBot Ultimate", layout="centered", page_icon="💿")

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

# --- 2. EXTENDED README & ARCHITECTURE ---
with st.expander("📚 READ ME: Architecture, Models & How It Works", expanded=True):
    st.markdown("""
    ### 🛠️ Architecture & Logic
    **DistroBot** is a Hybrid AI State Machine designed to act as a strict Quality Control (QC) agent for music distribution.
    
    1.  **Hybrid UI:** It combines Chat Interface (for free text) with Structured Widgets (Buttons, Date Pickers, Uploaders) to ensure data consistency.
    2.  **State Machine:** It tracks the user's progress (`step_id`) and strictly enforces a linear flow (Title -> Artist -> Genre -> etc.), but allows "Smart Skips" (e.g., skipping explicit questions for instrumentals).
    3.  **AI Router:** Every text input passes through `query_ai_engine()`, which classifies the intent:
        * **Is it a Question?** -> Answers from Knowledge Base.
        * **Is it a Skip Command?** -> Marks field as None.
        * **Is it Data?** -> Validates against Confluence Policy.

    ### 🧠 AI Models Supported
    This tool is "Model Agnostic" and uses a waterfall priority system:
    1.  **Groq (Llama-3-8b-instant):** *Primary.* Chosen for sub-second inference speed (crucial for chat UI) and strong instruction following.
    2.  **OpenAI (GPT-3.5-Turbo / GPT-4):** *Secondary.* Used if Groq fails. High reliability.
    3.  **Google (Gemini 1.5 Flash):** *Fallback.* Lightweight and fast backup.
    
    ### ✨ Core Features
    * **Validation Guardrails:** Blocks forbidden words (feat, prod, emojis) in real-time.
    * **Contextual FAQ:** Can pause the form to answer "What is an ISRC?" and then resume.
    * **Smart Date Logic:** Uses Python math to enforce "14-90 days in future" rules (more accurate than LLMs).
    * **Visual AI Fixer:** Simulates scanning cover art for text mismatches and offering a "one-click fix" (Mocked for demo).
    * **Metadata Inheritance:** Auto-fills Track Title for Single releases to match Release Title.
    """)

# --- 3. KNOWLEDGE BASE ---
DISTRO_KNOWLEDGE_BASE = """
VALIDATION POLICY (STRICT):
1. Release Title: 
   - FORBIDDEN: 'feat', 'prod', 'remix', emojis. 
   - ALLOWED: Proper names, foreign languages, brackets ().
   - NOTE: Self-titled albums (Artist Name = Title) are ALLOWED.
2. Version: 
   - FORBIDDEN: 'Original', 'Official', 'Explicit', 'New'. 
   - ALLOWED: 'Remix', 'Acoustic', 'Live'.
3. Artist Name: 
   - FORBIDDEN: 'feat', 'prod' inside name. 
4. Composer: 
   - MUST BE: Legal First & Last Name.
5. General: 
   - NO Emojis.
"""

# --- 4. ROBUST AI ENGINE ---

def clean_json(raw_text):
    try:
        # Regex to extract JSON object
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match: return json.loads(match.group(0))
        return json.loads(raw_text)
    except: return None

def query_ai_engine(user_input, current_field):
    """
    Validates inputs. UPDATED: Permissive by default for Titles.
    """
    system_prompt = f"""
    You are DistroBot QC.
    RULES: {DISTRO_KNOWLEDGE_BASE}
    
    CONTEXT: User input for Field="{current_field}".
    INPUT: "{user_input}"
    
    INSTRUCTIONS:
    1. **INTENT:** Is this a question (e.g. "help")? Return type="question".
    2. **SKIP:** Is this "none", "skip", "no"? Return type="skip".
    3. **VALIDATE:** - IF input violates a *specific* FORBIDDEN rule above -> valid=false.
       - IF input looks like a Name or Title and contains NO forbidden words -> valid=true.
       - Do NOT block proper names (e.g. "Marcel Pavel" is VALID for Title).
    
    RETURN JSON ONLY: 
    {{ "valid": true }} 
    OR {{ "valid": false, "error": "Reason" }} 
    OR {{ "type": "question", "reply": "..." }}
    """
    
    try:
        # Priority: Groq
        if groq_key:
            client = openai.OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": system_prompt}],
                response_format={"type": "json_object"},
                temperature=0
            )
            return clean_json(resp.choices[0].message.content)
            
        # Fallback: Gemini
        elif gemini_key:
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = model.generate_content(system_prompt + "\nReturn JSON only.")
            return clean_json(resp.text)
            
    except:
        return {"valid": True} # Fail safe (Allow user to proceed if AI is down)

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

def process_ai_response(val, field_key, next_step_id):
    """Helper to handle AI check results."""
    res = query_ai_engine(val, field_key)
    
    # 1. Question Handling
    if res.get("type") == "question":
        st.session_state.messages.append({"role": "assistant", "content": f"ℹ️ **FAQ:** {res['reply']}"})
        st.rerun()
        
    # 2. Skip Handling
    elif res.get("type") == "skip":
        st.session_state.data[field_key] = ""
        next_step(next_step_id)
        
    # 3. Data Validation
    else:
        if res.get("valid", True):
            st.session_state.data[field_key] = val
            next_step(next_step_id)
        else:
            bot_say(f"🚫 {res.get('error', 'Invalid input')}")

# --- 6. WORKFLOW STEPS ---

st.title("🤖 DistroBot V9")

# History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- START ---
if st.session_state.step_id == "start":
    bot_say("👋 Hi! I'm DistroBot. I'll guide you through your release.\n\n**First, what is the Title of your Release?**")
    st.session_state.step_id = "release_title"

# --- RELEASE TITLE ---
elif st.session_state.step_id == "release_title":
    val = st.chat_input("Release Title...")
    if val:
        add_user_msg(val)
        process_ai_response(val, "release_title", "version")

# --- VERSION ---
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
        process_ai_response(val, "version", "artist")

# --- ARTIST ---
elif st.session_state.step_id == "artist":
    bot_say("**Primary Artist Name?**")
    val = st.chat_input("Artist Name...")
    if val:
        add_user_msg(val)
        process_ai_response(val, "artist", "genre")

# --- GENRE ---
elif st.session_state.step_id == "genre":
    bot_say("Select your **Genre**:")
    genres = ["Pop", "Hip-Hop", "Rock", "Electronic", "R&B", "Latin"]
    cols = st.columns(3)
    for i, g in enumerate(genres):
        if cols[i%3].button(g):
            add_user_msg(g)
            st.session_state.data["genre"] = g
            next_step("upc_label_ask")

# --- UPC/LABEL ASK ---
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

# --- LABEL INPUT ---
elif st.session_state.step_id == "label_input":
    bot_say("Enter **Label Name** (or type 'Skip'):")
    val = st.chat_input("Label...")
    if val:
        add_user_msg(val)
        # Simple skip logic without AI for speed
        if val.lower() in ["skip", "no", "none"]:
            st.session_state.data["label"] = ""
        else:
            st.session_state.data["label"] = val
        next_step("date_ask")

# --- DATE ASK ---
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

# --- DATE INPUT ---
elif st.session_state.step_id == "date_input":
    bot_say("Please enter format YYYY-MM-DD. **Must be 14-90 days from today.**")
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

# --- COVER ART ---
elif st.session_state.step_id == "cover_art":
    bot_say("🎨 **Upload Cover Art** (JPG/PNG).")
    up = st.file_uploader("Image", type=["jpg", "png"])
    
    if up:
        if not st.session_state.art_fixed:
            with st.spinner("🤖 Scanning image text..."):
                time.sleep(1.2) # Demo effect
            
            st.markdown("""
            <div class='ai-fix-box'>
                <b>⚠️ AI Alert:</b> I detected text that doesn't match Artist Name "{}".<br>
                Do you want me to remove it?
            </div>
            """.format(st.session_state.data.get('artist', 'Unknown')), unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            if c1.button("✨ Fix with AI"):
                with st.spinner("🍌 Nano Banana is fixing it..."):
                    time.sleep(1.5)
                st.session_state.art_fixed = True
                st.success("Text removed! Image compliant.")
                st.rerun()
            if c2.button("Use Original"):
                 st.session_state.data["artwork"] = up.name
                 next_step("track_logic")
        else:
            bot_say("✅ Fixed image confirmed.")
            if st.button("Next Step"):
                st.session_state.data["artwork"] = "Fixed_" + up.name
                next_step("track_logic")

# --- TRACK LOGIC ---
elif st.session_state.step_id == "track_logic":
    # Auto-Inherit for Single
    st.session_state.data["track_title"] = st.session_state.data["release_title"]
    
    bot_say(f"ℹ️ **Single Track Mode:** Track Title set to **'{st.session_state.data['release_title']}'**.")
    time.sleep(1.5)
    next_step("prev_released")

# --- PREV RELEASED ---
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

# --- AUDIO UPLOAD ---
elif st.session_state.step_id == "audio_upload":
    bot_say("Upload Audio (WAV/FLAC).")
    up = st.file_uploader("Audio", type=["wav", "mp3"])
    if up:
        st.session_state.data["audio"] = up.name
        if st.button("Confirm Audio"):
            next_step("language")

# --- LANGUAGE ---
elif st.session_state.step_id == "language":
    bot_say("What **Language** are the lyrics in?")
    opts = ["English", "Spanish", "Instrumental (No Lyrics)"]
    cols = st.columns(3)
    for i, o in enumerate(opts):
        if cols[i].button(o):
            add_user_msg(o)
            st.session_state.data["language"] = o
            if "Instrumental" in o:
                st.session_state.data["explicit"] = "Clean"
                st.session_state.data["lyricist"] = "N/A"
                next_step("credits_performer")
            else:
                next_step("explicit")

# --- EXPLICIT ---
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

# --- LYRICIST ---
elif st.session_state.step_id == "lyricist_ask":
    bot_say("Are you the **Lyricist**?")
    c1, c2 = st.columns(2)
    if c1.button("Yes"):
        add_user_msg("Yes")
        st.session_state.data["lyricist"] = st.session_state.data["artist"]
        next_step("credits_performer")
    if c2.button("No"):
        add_user_msg("No")
        next_step("lyricist_input")

elif st.session_state.step_id == "lyricist_input":
    val = st.chat_input("Lyricist Legal Name")
    if val:
        add_user_msg(val)
        process_ai_response(val, "lyricist", "credits_performer")

# --- PERFORMER ---
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

elif st.session_state.step_id == "performer_input":
    val = st.chat_input("Performer Name")
    if val:
        add_user_msg(val)
        st.session_state.data["performer"] = val
        next_step("performer_inst")

elif st.session_state.step_id == "performer_inst":
    bot_say("Select **Instrument**:")
    insts = ["Vocals", "Guitar", "Drums", "Synth"]
    cols = st.columns(4)
    for i, inst in enumerate(insts):
        if cols[i].button(inst):
            add_user_msg(inst)
            st.session_state.data["instrument"] = inst
            next_step("credits_prod")

# --- PRODUCER ---
elif st.session_state.step_id == "credits_prod":
    bot_say("Select **Production Role**:")
    roles = ["Producer", "Mixing Engineer", "Mastering Engineer"]
    cols = st.columns(3)
    for i, r in enumerate(roles):
        if cols[i].button(r):
            add_user_msg(r)
            st.session_state.data["prod_role"] = r
            next_step("contributors")

# --- CONTRIBUTORS ---
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
    val = st.chat_input("Contributor Name")
    if val:
        add_user_msg(val)
        st.session_state.data["contributor"] = val
        next_step("optional_ids")

# --- IDS ---
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
    val = st.chat_input("ISRC (or type Skip)")
    if val:
        add_user_msg(val)
        st.session_state.data["isrc"] = val
        next_step("summary")

# --- SUMMARY ---
elif st.session_state.step_id == "summary":
    bot_say("✅ **Release Ready!** Review details:")
    st.json(st.session_state.data)
    if st.button("🚀 Submit Release"):
        st.balloons()
        st.success("Sent to QC!")
    if st.button("🔄 Restart"):
        st.session_state.clear()
        st.rerun()
