import streamlit as st
import openai
import google.generativeai as genai
import json
import re

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="DistroBot Final", layout="centered", page_icon="💿")

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
        .chat-bubble-assistant {
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 15px;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# Retrieve Keys
openai_key = st.secrets.get("OPENAI_API_KEY")
gemini_key = st.secrets.get("GEMINI_API_KEY")
groq_key = st.secrets.get("GROQ_API_KEY")

if gemini_key:
    genai.configure(api_key=gemini_key)

# --- 2. KNOWLEDGE BASE & RULES ---
DISTRO_KNOWLEDGE_BASE = """
GENERAL FAQ:
- **Spotify/Apple:** Yes, we distribute to all major platforms including Spotify, Apple Music, TikTok, and Amazon.
- **Release Timeline:** We recommend setting a release date at least 4 weeks in advance. Fast releases take 2-5 days.
- **Payouts:** Royalties are paid 2-3 months after the stream happens.
- **UPC/ISRC:** We provide these for free if you don't have them.
- **Cover Art:** Must be 3000x3000px, Square, JPG/PNG.

VALIDATION RULES (STRICT):
1. Release Title: 
   - ALLOWED: Letters, numbers, spaces, hyphens, brackets ().
   - FORBIDDEN: 'feat', 'prod', 'remix', emojis, special chars like @#$%^&*.
   -
2. Version: 
   - FORBIDDEN: 'Original', 'Official', 'Explicit', 'New'. 
   -
3. Artist Name: 
   - FORBIDDEN: 'feat', 'prod' inside the name. No brackets. 
   -
4. Composer: 
   - MUST BE: Legal First & Last Name (e.g., 'John Doe').
   - FORBIDDEN: Single names ('Cher'), Alias names ('DJ Snake'), 'beats', 'music'.
   -
"""

# --- 3. WORKFLOW DEFINITION ---
WORKFLOW_STEPS = [
    {
        "id": "release_title",
        "prompt": "Let's start your release! 🚀\n\n**What is the Title of your Single or Album?**",
        "tip": "💡 **Tip:** Don't include 'feat.' or 'prod.' here. We have separate fields for that later!",
        "type": "text"
    },
    {
        "id": "version",
        "prompt": "Is there a specific **Version**? (e.g., Acoustic, Remix, Radio Edit).\nIf it's the original, click 'Skip'.",
        "tip": "💡 **Tip:** Avoid words like 'Original' or 'Official'. Just leave it empty for the main version.",
        "type": "text",
        "optional": True
    },
    {
        "id": "artist_name",
        "prompt": "Got it. **What is the Primary Artist Name?**",
        "tip": "💡 **Tip:** Use the name exactly as it appears on Spotify/Apple Music.",
        "type": "text"
    },
    {
        "id": "genre",
        "prompt": "What is the primary **Genre**?",
        "tip": "💡 **Tip:** Choosing the accurate genre helps with store placement.",
        "type": "selection",
        "options": ["Pop", "Hip-Hop/Rap", "Rock", "Electronic", "R&B", "Latin", "Country", "Jazz", "Classical", "Alternative"]
    },
    {
        "id": "release_date",
        "prompt": "When should this go live?",
        "tip": "💡 **Tip:** Picking a date 3-4 weeks away gives you time to pitch to playlists.",
        "type": "selection",
        "options": ["As Soon As Possible", "Specific Date"]
    },
    {
        "id": "artwork",
        "prompt": "🎨 **Upload Cover Art** (3000x3000px, JPG/PNG).",
        "tip": "💡 **Tip:** No social media handles, URLs, or blurry images.",
        "type": "file",
        "file_types": ["jpg", "png", "jpeg"]
    },
    {
        "id": "track_title",
        "prompt": "Now for audio. **What is the Track Title?**",
        "tip": "💡 **Tip:** For single releases, this usually matches the Release Title.",
        "type": "text"
    },
    {
        "id": "audio_file",
        "prompt": "Upload your audio file (WAV/FLAC).",
        "tip": "💡 **Tip:** We recommend 16-bit or 24-bit WAV files.",
        "type": "file",
        "file_types": ["wav", "flac", "mp3"]
    },
    {
        "id": "explicit",
        "prompt": "Does this track contain **Explicit Content**?",
        "type": "selection",
        "options": ["Clean", "Explicit", "Instrumental"]
    },
    {
        "id": "composer",
        "prompt": "Almost done. **Who is the Composer?**",
        "tip": "💡 **Important:** You MUST use a **Legal First & Last Name** (e.g., 'John Smith'). Required for royalties.",
        "type": "text"
    }
]

# --- 4. ROBUST AI ENGINE ---

def clean_json(raw_text):
    """Robustly extracts JSON from LLM output, handling markdown wrappers."""
    try:
        # Regex to find JSON block { ... }
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(raw_text)
    except:
        return None

def query_ai_engine(user_input, current_field):
    """
    Classifies input as Question vs Answer, then Validates if Answer.
    """
    system_prompt = f"""
    You are DistroBot, a QC Expert.
    
    KNOWLEDGE BASE:
    {DISTRO_KNOWLEDGE_BASE}
    
    CONTEXT:
    User is on step: "{current_field}"
    User Input: "{user_input}"
    
    INSTRUCTIONS (EXECUTE IN ORDER):
    1. **INTENT CHECK:** Is the user asking a general question (e.g., "What is this?", "Help", "Will it be on Spotify?") OR giving a command ("Skip", "Next")?
       - If YES: Output type="question" and answer it.
       
    2. **VALIDATION CHECK:** If it is NOT a question, assume it is the input value for "{current_field}".
       - Validate it strictly against VALIDATION RULES.
       - "December Throwback" -> VALID title.
       - "My Song (feat. Drake)" -> INVALID title.
       - "John" -> INVALID Composer.
       
    OUTPUT JSON ONLY:
    One of these two formats:
    A) {{ "type": "question", "reply": "Answer from knowledge base..." }}
    B) {{ "type": "data", "valid": true/false, "error": "Reason if invalid" }}
    """
    
    try:
        # Priority 1: Groq
        if groq_key:
            client = openai.OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "system", "content": system_prompt}],
                response_format={"type": "json_object"},
                temperature=0
            )
            return clean_json(resp.choices[0].message.content)
            
        # Priority 2: Gemini
        elif gemini_key:
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = model.generate_content(system_prompt + "\nReturn JSON only.")
            return clean_json(resp.text)
            
    except Exception as e:
        # Fail safe
        return {"type": "data", "valid": True}

# --- 5. APP LOGIC ---

if "messages" not in st.session_state:
    st.session_state.messages = []
if "step_index" not in st.session_state:
    st.session_state.step_index = 0
if "data" not in st.session_state:
    st.session_state.data = {}

def bot_say(text):
    with st.chat_message("assistant"):
        st.markdown(text)

def handle_input(user_value, field_id):
    # 1. Show user message
    st.session_state.messages.append({"role": "user", "content": str(user_value)})
    
    # 2. Process with AI
    with st.spinner("Analyzing..."):
        ai_result = query_ai_engine(str(user_value), field_id)
    
    # 3. Handle NULL result (API Failure)
    if not ai_result:
        # Allow pass-through if AI is down
        st.session_state.data[field_id] = user_value
        st.session_state.step_index += 1
        st.rerun()

    # 4. Handle Logic
    if ai_result.get("type") == "question":
        # It's a question -> Answer and stay on same step
        st.session_state.messages.append({"role": "assistant", "content": f"ℹ️ **FAQ:** {ai_result['reply']}"})
        st.rerun()
        
    else:
        # It's data -> Check validity
        if ai_result.get("valid"):
            st.session_state.data[field_id] = user_value
            st.session_state.step_index += 1
            st.rerun()
        else:
            error = ai_result.get('error', 'Invalid input format.')
            st.session_state.messages.append({"role": "assistant", "content": f"🚫 **Wait:** {error}"})
            st.rerun()

# --- 6. RENDER LOOP ---

st.title("🤖 DistroBot")
st.progress(min(st.session_state.step_index / len(WORKFLOW_STEPS), 1.0))

# Display History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Completion Check
if st.session_state.step_index >= len(WORKFLOW_STEPS):
    bot_say("✅ **Release Ready for QC!** Summary:")
    st.json(st.session_state.data)
    if st.button("🚀 Submit Release"):
        st.balloons()
        st.success("Sent to distribution!")
    if st.button("🔄 Start Over"):
        st.session_state.clear()
        st.rerun()
    st.stop()

# Current Step Info
current_step = WORKFLOW_STEPS[st.session_state.step_index]

# Render Tip
if "tip" in current_step:
    st.markdown(f"<div class='info-box'>{current_step['tip']}</div>", unsafe_allow_html=True)

# Render Prompt (if needed)
if not st.session_state.messages or st.session_state.messages[-1]["role"] == "user":
    bot_say(current_step["prompt"])

# Render Inputs
if current_step["type"] == "selection":
    cols = st.columns(3)
    for i, opt in enumerate(current_step["options"]):
        if cols[i % 3].button(opt, key=f"btn_{i}"):
            handle_input(opt, current_step["id"])

elif current_step["type"] == "file":
    up = st.file_uploader(f"Upload {current_step['id']}", type=current_step["file_types"], key=f"f_{current_step['id']}")
    if up and st.button("Confirm Upload", key=f"c_{current_step['id']}"):
        handle_input(up.name, current_step["id"])

elif current_step["type"] == "text":
    if current_step.get("optional") and st.button("Skip", key=f"s_{current_step['id']}"):
        handle_input("None", current_step["id"])
        
    val = st.chat_input(f"Type answer...")
    if val:
        handle_input(val, current_step["id"])
