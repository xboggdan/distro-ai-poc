import streamlit as st
import openai
import google.generativeai as genai
import json
import time
from datetime import date, timedelta

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="DistroBot Demo", layout="centered", page_icon="💿")

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
    </style>
""", unsafe_allow_html=True)

# Retrieve Keys
openai_key = st.secrets.get("OPENAI_API_KEY")
gemini_key = st.secrets.get("GEMINI_API_KEY")
groq_key = st.secrets.get("GROQ_API_KEY")

if gemini_key:
    genai.configure(api_key=gemini_key)

# --- 2. KNOWLEDGE BASE (THE BRAIN) ---
# Combined Confluence Rules + General Industry FAQ
DISTRO_KNOWLEDGE_BASE = """
GENERAL DISTRIBUTION FAQ:
- **Release Timeline:** We recommend setting a release date at least 4 weeks in advance to pitch for playlists (Spotify/Apple). Faster releases take 2-5 days to go live.
- **Payouts/Royalties:** Stores usually pay out 2-3 months after the stream happens (e.g., January streams are paid in April).
- **UPC:** A barcode for the whole product (Album/Single). We assign one for free if you don't have it.
- **ISRC:** A unique ID for a specific recording (Track). Used to track sales/streams.
- **Cover Art:** Must be 3000x3000px, RGB Color space, JPG/PNG. No social handles, blurry text, or brands.
- **Composer Names:** Must use Legal First & Last Name for collection societies. "Beats by Dre" is not valid.
- **Explicit Content:** If you have swears, mark it Explicit. If clean, mark Clean.

VALIDATION RULES (STRICT):
1. Release Title: No 'feat', 'prod', 'remix'. No emojis. Brackets () are allowed.
2. Version: No special chars. Forbidden words: 'new', 'featuring', 'feat', 'Official', 'Explicit'.
3. Artist Name: No 'feat', 'prod' inside name. No brackets.
4. Composer: Must be Legal First & Last Name. No 'beats', 'music'.
5. General: No emojis in any field.
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
        "tip": "💡 **Tip:** Use the name exactly as it appears on Spotify/Apple Music to link profiles correctly.",
        "type": "text"
    },
    {
        "id": "genre",
        "prompt": "What is the primary **Genre**?",
        "tip": "💡 **Tip:** Choosing the most accurate genre helps with store placement.",
        "type": "selection",
        "options": ["Pop", "Hip-Hop/Rap", "Rock", "Electronic", "R&B", "Latin", "Country", "Jazz", "Classical", "Alternative"]
    },
    {
        "id": "release_date",
        "prompt": "When should this go live?",
        "tip": "💡 **Tip:** Picking a date 3-4 weeks away gives you time to pitch to editorial playlists.",
        "type": "selection",
        "options": ["As Soon As Possible", "Specific Date"]
    },
    {
        "id": "upc_label",
        "prompt": "Do you have a **Label Name**? (Optional)",
        "tip": "💡 **Tip:** If you are independent, you can use your artist name or leave this blank.",
        "type": "text",
        "optional": True
    },
    {
        "id": "artwork",
        "prompt": "🎨 **Upload Cover Art** (3000x3000px, JPG/PNG).",
        "tip": "💡 **Tip:** No social media handles, website URLs, or blurry images. Stores will reject them!",
        "type": "file",
        "file_types": ["jpg", "png", "jpeg"]
    },
    {
        "id": "track_title",
        "prompt": "Now for audio details. **What is the Track Title?**",
        "tip": "💡 **Tip:** For single releases, this must match the Release Title.",
        "type": "text"
    },
    {
        "id": "audio_file",
        "prompt": "Upload your audio file (WAV/FLAC preferred).",
        "tip": "💡 **Tip:** We recommend 16-bit or 24-bit WAV files (44.1kHz).",
        "type": "file",
        "file_types": ["wav", "flac", "mp3"]
    },
    {
        "id": "explicit",
        "prompt": "Does this track contain **Explicit Content**?",
        "tip": "💡 **Tip:** 'Explicit' means it contains strong language or references to violence/drugs.",
        "type": "selection",
        "options": ["Clean", "Explicit", "Instrumental"]
    },
    {
        "id": "language",
        "prompt": "What **Language** are the lyrics in?",
        "tip": "💡 **Tip:** Select 'Instrumental' if there are no lyrics.",
        "type": "selection",
        "options": ["English", "Spanish", "French", "German", "Japanese", "No Lyrics (Instrumental)"]
    },
    {
        "id": "composer",
        "prompt": "Almost done. **Who is the Composer?**",
        "tip": "💡 **Important:** You MUST use a **Legal First & Last Name** (e.g., 'John Smith', not 'DJ Snake'). This is required for publishing royalties.",
        "type": "text"
    }
]

# --- 4. INTELLIGENT AI ENGINE ---

def query_ai_engine(user_input, current_field):
    """
    Decides if the user is answering the question OR asking a question.
    """
    system_prompt = f"""
    You are DistroBot, a helpful music distribution assistant.
    
    KNOWLEDGE BASE:
    {DISTRO_KNOWLEDGE_BASE}
    
    CURRENT CONTEXT:
    The user is currently on step: "{current_field}".
    
    TASK:
    Analyze the User Input: "{user_input}"
    
    1. INTENT DETECTION: Is the user asking a question (e.g., "What is ISRC?", "When do I get paid?", "Help")?
       OR is the user providing the value for the field?
       
    2. IF QUESTION:
       - Answer the question helpfully using the KNOWLEDGE BASE.
       - JSON Output: {{"action": "answer_question", "response": "Your answer here...", "valid": false}}
       
    3. IF VALUE/ANSWER:
       - Validate the value against the VALIDATION RULES for "{current_field}".
       - JSON Output: {{"action": "validate_input", "valid": true, "error": ""}} 
       - OR {{"action": "validate_input", "valid": false, "error": "Reason for rejection"}}
       
    OUTPUT JSON ONLY.
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
            return json.loads(resp.choices[0].message.content)
            
        # Fallback: Gemini
        elif gemini_key:
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = model.generate_content(system_prompt + "\nReturn JSON only.")
            text = resp.text.replace("```json", "").replace("```", "")
            return json.loads(text)

    except Exception as e:
        # Fallback if AI fails: Assume it's a valid input
        return {"action": "validate_input", "valid": True, "error": ""}

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

def handle_user_input(user_value, field_id):
    # 1. Show user message
    st.session_state.messages.append({"role": "user", "content": str(user_value)})
    
    # 2. Call AI Engine
    ai_result = query_ai_engine(str(user_value), field_id)
    
    # 3. Logic Branch
    if ai_result["action"] == "answer_question":
        # It was a question! Answer it, but DON'T advance step.
        bot_response = f"ℹ️ **FAQ:** {ai_result['response']}\n\nNow, let's get back to it. {WORKFLOW_STEPS[st.session_state.step_index]['prompt']}"
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        st.rerun()
        
    elif ai_result["action"] == "validate_input":
        # It was an input. Check validity.
        if ai_result["valid"]:
            # Success! Save and move on.
            st.session_state.data[field_id] = user_value
            st.session_state.step_index += 1
            st.rerun()
        else:
            # Validation Error
            error_msg = f"🚫 **Wait:** {ai_result.get('error', 'Invalid input.')}"
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.rerun()

# --- 6. MAIN RENDER LOOP ---

st.title("🤖 DistroBot")
st.progress(min(st.session_state.step_index / len(WORKFLOW_STEPS), 1.0))

# Display History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Check Completion
if st.session_state.step_index >= len(WORKFLOW_STEPS):
    bot_say("✅ **Release Ready for Review!** Here is the summary:")
    st.json(st.session_state.data)
    
    col1, col2 = st.columns(2)
    if col1.button("🚀 Submit to QC Team"):
        st.balloons()
        st.success("Submission Sent! Reference #99283")
    if col2.button("🔄 Start New Release"):
        st.session_state.clear()
        st.rerun()
    st.stop()

# Get Current Step
current_step = WORKFLOW_STEPS[st.session_state.step_index]

# 1. Show Tip (Contextual Help)
if "tip" in current_step:
    st.markdown(f"<div class='info-box'>{current_step['tip']}</div>", unsafe_allow_html=True)

# 2. Show Prompt (Only if last message wasn't this prompt)
if not st.session_state.messages or st.session_state.messages[-1]["role"] == "user":
    bot_say(current_step["prompt"])

# 3. Render Inputs
if current_step["type"] == "selection":
    cols = st.columns(3)
    for i, option in enumerate(current_step["options"]):
        if cols[i % 3].button(option, key=f"btn_{current_step['id']}_{i}"):
            handle_user_input(option, current_step["id"])

elif current_step["type"] == "file":
    uploaded = st.file_uploader(f"Upload {current_step['id']}", type=current_step["file_types"], key=f"file_{current_step['id']}")
    if uploaded and st.button("Confirm Upload", key=f"confirm_{current_step['id']}"):
        handle_user_input(uploaded.name, current_step["id"])

elif current_step["type"] == "text":
    # Optional Skip Button
    if current_step.get("optional"):
        if st.button("Skip this step", key=f"skip_{current_step['id']}"):
            handle_user_input("None", current_step["id"])

    # Chat Input
    user_text = st.chat_input(f"Type answer for {current_step['id']}...")
    if user_text:
        handle_user_input(user_text, current_step["id"])
