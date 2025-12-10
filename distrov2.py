import streamlit as st
import openai
import google.generativeai as genai
import json
import re

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="DistroBot AI Demo", layout="centered", page_icon="💿")

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
        .how-it-works {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #ddd;
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

# --- 2. HOW IT WORKS (ONBOARDING) ---
with st.expander("📚 READ ME: How it Works & Testing Guide", expanded=True):
    st.markdown("""
    ### 🤖 DistroBot Architecture
    This is a **Hybrid AI Form Assistant** designed to replace complex music distribution wizards.
    
    * **The Brain:** Powered by **Groq (Llama-3-8b)** for sub-second inference.
    * **The Logic:** Uses a **State Machine** combined with an **AI Validator**.
    * **The Guardrails:** Validates inputs against a "Confluence Policy Doc" to prevent metadata errors (e.g., blocking "feat." in artist names).
    
    ### 🧪 How to Test This Demo
    
    **Scenario 1: The "Happy Path" (Valid Data)**
    1.  **Title:** Enter `Summer Vibes`
    2.  **Version:** Type `Remix` (or click Skip)
    3.  **Artist:** Enter `The Band`
    4.  **Composer:** Enter `John Smith` (Legal Name)
    * *Result:* Success! ✅
    
    **Scenario 2: The "Validation Error" (QC Block)**
    1.  **Title:** Enter `My Song (feat. Drake)`
    2.  **Artist:** Enter `DJ Khaled feat. Justin`
    * *Result:* The bot will **BLOCK** you because "feat" belongs in the contributor field, not the main field.
    
    **Scenario 3: The "Contextual FAQ" (AI Reasoning)**
    1.  **Any Step:** Ask a question like *"When will I get paid?"* or *"What is a UPC?"*
    2.  *Result:* The bot will pause, answer your question from its Knowledge Base, and then ask for the input again.
    
    **Scenario 4: The "Smart Skip"**
    1.  **Version:** Type `I don't have one` or `leave empty`.
    2.  *Result:* The AI understands you want to **Skip** the optional field and proceeds.
    """)

# --- 3. KNOWLEDGE BASE & RULES ---
DISTRO_KNOWLEDGE_BASE = """
GENERAL FAQ:
- **Spotify/Apple:** Yes, we distribute to all major platforms.
- **Payouts:** Royalties are paid 2-3 months after the stream happens.
- **UPC/ISRC:** We provide these for free.
- **Cover Art:** Must be 3000x3000px, Square, JPG/PNG.

VALIDATION RULES (STRICT):
1. Release Title: 
   - FORBIDDEN: 'feat', 'prod', 'remix', emojis, special chars like @#$%^&*. Brackets () are allowed.
2. Version: 
   - ALLOWED: 'Remix', 'Radio Edit', 'Acoustic', 'Live', 'Instrumental'.
   - FORBIDDEN: 'Original', 'Official', 'Explicit', 'New'.
3. Artist Name: 
   - FORBIDDEN: 'feat', 'prod' inside the name. No brackets.
4. Composer: 
   - MUST BE: Legal First & Last Name (e.g., 'John Doe').
   - FORBIDDEN: Single names, Alias names ('DJ Snake'), 'beats', 'music'.
"""

# --- 4. WORKFLOW DEFINITION ---
WORKFLOW_STEPS = [
    {
        "id": "release_title",
        "prompt": "Let's start! 🚀\n\n**What is the Title of your Single or Album?**",
        "tip": "💡 **Tip:** Don't include 'feat.' or 'prod.' here.",
        "type": "text"
    },
    {
        "id": "version",
        "prompt": "Is there a specific **Version**? (e.g., Remix, Acoustic).\nIf it's the original, just click 'Skip'.",
        "tip": "💡 **Tip:** Valid versions are 'Remix', 'Radio Edit', etc. Don't write 'Original'.",
        "type": "text",
        "optional": True
    },
    {
        "id": "artist_name",
        "prompt": "Got it. **What is the Primary Artist Name?**",
        "tip": "💡 **Tip:** Use the name exactly as it appears on Spotify.",
        "type": "text"
    },
    {
        "id": "genre",
        "prompt": "What is the primary **Genre**?",
        "type": "selection",
        "options": ["Pop", "Hip-Hop/Rap", "Rock", "Electronic", "R&B", "Latin", "Country", "Alternative"]
    },
    {
        "id": "release_date",
        "prompt": "When should this go live?",
        "type": "selection",
        "options": ["As Soon As Possible", "Specific Date"]
    },
    {
        "id": "artwork",
        "prompt": "🎨 **Upload Cover Art** (3000x3000px, JPG/PNG).",
        "type": "file",
        "file_types": ["jpg", "png", "jpeg"]
    },
    {
        "id": "track_title",
        "prompt": "Now for audio. **What is the Track Title?**",
        "tip": "💡 **Tip:** For singles, this usually matches the Release Title.",
        "type": "text"
    },
    {
        "id": "audio_file",
        "prompt": "Upload your audio file (WAV/FLAC).",
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

# --- 5. ROBUST AI ENGINE ---

def clean_json(raw_text):
    try:
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match: return json.loads(match.group(0))
        return json.loads(raw_text)
    except: return None

def query_ai_engine(user_input, current_field, is_optional):
    """
    Intelligent Router: Detects Skip, Question, or Validation.
    """
    system_prompt = f"""
    You are DistroBot QC.
    RULES: {DISTRO_KNOWLEDGE_BASE}
    
    CONTEXT: Step="{current_field}", Input="{user_input}", Optional={is_optional}
    
    INSTRUCTIONS:
    1. **SKIP DETECTION:** If input is "none", "skip", "no", "leave empty", "n/a":
       - If Optional=True: Output {{"type": "skip", "valid": true}}
       - If Optional=False: Output {{"type": "data", "valid": false, "error": "This field is required."}}
       
    2. **FAQ DETECTION:** If user asks a question (e.g., "What is this?"):
       - Output {{"type": "question", "reply": "Answer from rules..."}}
       
    3. **VALIDATION:** Validate input against RULES for "{current_field}".
       - "Remix" is VALID for Version. "Original" is INVALID for Version.
       - "feat" is INVALID for Title/Artist.
       - Output {{"type": "data", "valid": true}} OR {{"type": "data", "valid": false, "error": "Reason"}}
       
    RETURN JSON ONLY.
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
            
        elif gemini_key:
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = model.generate_content(system_prompt + "\nReturn JSON only.")
            return clean_json(resp.text)
            
    except Exception:
        return {"type": "data", "valid": True} # Fail open

# --- 6. APP LOGIC ---

if "messages" not in st.session_state:
    st.session_state.messages = []
if "step_index" not in st.session_state:
    st.session_state.step_index = 0
if "data" not in st.session_state:
    st.session_state.data = {}

def bot_say(text):
    with st.chat_message("assistant"):
        st.markdown(text)

def handle_input(user_value, field_id, optional=False):
    st.session_state.messages.append({"role": "user", "content": str(user_value)})
    
    with st.spinner("🤖 DistroBot Analyzing..."):
        ai_result = query_ai_engine(str(user_value), field_id, optional)
    
    if not ai_result: # API Error Fallback
        st.session_state.data[field_id] = user_value
        st.session_state.step_index += 1
        st.rerun()

    # Routing Logic
    msg_type = ai_result.get("type")
    
    if msg_type == "question":
        st.session_state.messages.append({"role": "assistant", "content": f"ℹ️ **FAQ:** {ai_result['reply']}"})
        st.rerun()
        
    elif msg_type == "skip":
        st.session_state.data[field_id] = "None"
        st.session_state.step_index += 1
        st.rerun()
        
    else: # Data Validation
        if ai_result.get("valid"):
            st.session_state.data[field_id] = user_value
            st.session_state.step_index += 1
            st.rerun()
        else:
            error = ai_result.get('error', 'Invalid input.')
            st.session_state.messages.append({"role": "assistant", "content": f"🚫 **Wait:** {error}"})
            st.rerun()

# --- 7. RENDER LOOP ---

st.title("🤖 DistroBot Demo")
st.progress(min(st.session_state.step_index / len(WORKFLOW_STEPS), 1.0))

# History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Completion
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

# Current Interaction
current_step = WORKFLOW_STEPS[st.session_state.step_index]

if "tip" in current_step:
    st.markdown(f"<div class='info-box'>{current_step['tip']}</div>", unsafe_allow_html=True)

if not st.session_state.messages or st.session_state.messages[-1]["role"] == "user":
    bot_say(current_step["prompt"])

# Inputs
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
    is_opt = current_step.get("optional", False)
    if is_opt and st.button("Skip", key=f"s_{current_step['id']}"):
        handle_input("None", current_step["id"], True)
        
    val = st.chat_input(f"Type answer...")
    if val:
        handle_input(val, current_step["id"], is_opt)
