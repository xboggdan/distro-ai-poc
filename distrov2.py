import streamlit as st
import openai
import google.generativeai as genai
import json
import time
from datetime import date

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="DistroBot Smart Chat", layout="centered", page_icon="🎵")

# Custom CSS for "Smart Options" buttons to look like chat pills
st.markdown("""
    <style>
        .stButton > button {
            border-radius: 20px;
            border: 1px solid #E0E0E0;
            background-color: #F8F9FA;
            color: #31333F;
            padding: 5px 15px;
            font-size: 14px;
            margin-right: 5px;
        }
        .stButton > button:hover {
            border-color: #FF4B4B;
            color: #FF4B4B;
        }
        .chat-bubble {
            padding: 15px;
            border-radius: 15px;
            background-color: #f0f2f6;
            margin-bottom: 10px;
            display: inline-block;
        }
        .user-bubble {
            background-color: #e7f3ff;
            text-align: right;
            float: right;
        }
    </style>
""", unsafe_allow_html=True)

# Retrieve Keys
openai_key = st.secrets.get("OPENAI_API_KEY")
gemini_key = st.secrets.get("GEMINI_API_KEY")
groq_key = st.secrets.get("GROQ_API_KEY")

if gemini_key:
    genai.configure(api_key=gemini_key)

# --- 2. WORKFLOW DEFINITION (THE MAP) ---
# This defines the Linear Flow. 
# Types: 'text', 'selection', 'date', 'file', 'bool'

WORKFLOW_STEPS = [
    {
        "id": "release_title",
        "prompt": "Let's start your release! 🚀\n\n**What is the Title of your Single or Album?**",
        "type": "text",
        "validation_rule": "No 'feat', 'prod', or special chars like @#$%. Brackets () are okay."
    },
    {
        "id": "version",
        "prompt": "Is there a specific **Version** for this release?\n(e.g., Acoustic, Remix, Live). If it's the original, just click 'Skip'.",
        "type": "text",
        "optional": True,
        "validation_rule": "No 'Original', 'Explicit', 'Official'."
    },
    {
        "id": "artist_name",
        "prompt": "Got it. **What is the Primary Artist Name?**",
        "type": "text",
        "validation_rule": "Must be the artist name only. Do not add 'feat. Drake' here."
    },
    {
        "id": "genre",
        "prompt": "Nice name. **What is the primary Genre?**",
        "type": "selection",
        "options": ["Pop", "Hip-Hop/Rap", "Rock", "Electronic", "R&B", "Latin", "Country", "Jazz", "Classical", "Alternative"]
    },
    {
        "id": "release_date",
        "prompt": "When should this go live?",
        "type": "selection",
        "options": ["As Soon As Possible", "Specific Date"]
    },
    {
        "id": "upc_label",
        "prompt": "Do you have a Label Name? (Optional)",
        "type": "text",
        "optional": True,
        "validation_rule": "Standard text only."
    },
    {
        "id": "artwork",
        "prompt": "🎨 **Time for artwork.**\nPlease upload a square (1:1) image, at least 3000x3000px.",
        "type": "file",
        "file_types": ["jpg", "png", "jpeg"]
    },
    {
        "id": "track_title",
        "prompt": "Now for the audio. **What is the Track Title?**",
        "type": "text",
        "validation_rule": "Must match Release Title if it's a single."
    },
    {
        "id": "audio_file",
        "prompt": "Upload your high-quality audio file (WAV/FLAC).",
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
        "id": "language",
        "prompt": "What language are the lyrics in?",
        "type": "selection",
        "options": ["English", "Spanish", "French", "German", "Japanese", "No Lyrics (Instrumental)"]
    },
    {
        "id": "composer",
        "prompt": "Almost done. **Who is the Composer?**\n(Legal First & Last Name required for royalties).",
        "type": "text",
        "validation_rule": "Must be 'First Last'. No 'beats' or aliases."
    }
]

# --- 3. VALIDATION ENGINE ---
QC_RULES = """
RULES:
1. Release Title: No 'feat', 'prod', 'remix'. No emojis.
2. Artist Name: No 'feat', 'prod' inside name.
3. Composer: Must be Legal First & Last Name. No 'beats', 'music'.
4. General: No emojis in any field.
"""

def validate_with_ai(field_name, user_value):
    """Sends text input to LLM for strict validation against Confluence rules."""
    if not user_value: return True, ""
    
    system_prompt = f"""
    You are a QC Validator. POLICY: {QC_RULES}
    Check Field: "{field_name}" Value: "{user_value}"
    Output JSON: {{"valid": true, "error": ""}} or {{"valid": false, "error": "Reason"}}
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
            data = json.loads(resp.choices[0].message.content)
            return data["valid"], data.get("error", "Invalid format")
    except:
        return True, "" # Fail open if AI is down
    return True, ""

# --- 4. APP LOGIC ---

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "step_index" not in st.session_state:
    st.session_state.step_index = 0
if "data" not in st.session_state:
    st.session_state.data = {}
if "processing" not in st.session_state:
    st.session_state.processing = False

# Helper to Advance Step
def advance_step(user_input_display, key, value):
    # 1. Add User Answer to Chat
    st.session_state.messages.append({"role": "user", "content": user_input_display})
    # 2. Save Data
    st.session_state.data[key] = value
    # 3. Move Index
    st.session_state.step_index += 1
    # 4. Rerun to show next bot question
    st.rerun()

def bot_say(text):
    with st.chat_message("assistant"):
        st.markdown(text)

# --- 5. MAIN RENDER LOOP ---

st.title("🤖 DistroBot Assistant")
st.progress(min(st.session_state.step_index / len(WORKFLOW_STEPS), 1.0))

# 1. Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 2. Check if Flow is Complete
if st.session_state.step_index >= len(WORKFLOW_STEPS):
    bot_say("✅ **That's everything!** Here is your release summary:")
    
    # Summary Card
    with st.container():
        st.markdown("### 💿 Release Preview")
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.data.get("artwork"):
                st.image(st.session_state.data["artwork"], caption="Cover Art", width=250)
            else:
                st.info("No Artwork Uploaded")
        with col2:
            st.write(f"**Title:** {st.session_state.data.get('release_title')}")
            st.write(f"**Artist:** {st.session_state.data.get('artist_name')}")
            st.write(f"**Genre:** {st.session_state.data.get('genre')}")
            st.write(f"**Release Date:** {st.session_state.data.get('release_date')}")
            st.write(f"**Composer:** {st.session_state.data.get('composer')}")

    if st.button("🚀 Submit to QC"):
        st.balloons()
        st.success("Release Submitted Successfully!")
    
    if st.button("🔄 Start Over"):
        st.session_state.clear()
        st.rerun()

    st.stop() # Stop execution here

# 3. Get Current Step Configuration
current_step = WORKFLOW_STEPS[st.session_state.step_index]

# 4. Display Bot's Question (Only if not already displayed for this step)
# We assume the last message in history was the user's answer to the PREVIOUS step.
# So we render the current prompt now.
bot_say(current_step["prompt"])

# 5. RENDER DYNAMIC INPUTS BASED ON TYPE

# --- TYPE: SELECTION (Smart Buttons) ---
if current_step["type"] == "selection":
    st.write("👉 **Select an option:**")
    cols = st.columns(3) # create a grid of buttons
    options = current_step["options"]
    
    for i, option in enumerate(options):
        # Distribute buttons across columns
        if cols[i % 3].button(option, key=f"btn_{current_step['id']}_{i}"):
            advance_step(option, current_step['id'], option)

# --- TYPE: FILE UPLOAD ---
elif current_step["type"] == "file":
    uploaded_file = st.file_uploader(f"Upload {current_step['id']}", type=current_step["file_types"], key=f"file_{current_step['id']}")
    
    if uploaded_file:
        # Show preview
        if "image" in uploaded_file.type:
            st.image(uploaded_file, width=200)
        
        if st.button("Confirm Upload", key=f"confirm_{current_step['id']}"):
            advance_step(f"Uploaded {uploaded_file.name}", current_step['id'], uploaded_file)

# --- TYPE: TEXT INPUT (Standard Chat Box) ---
elif current_step["type"] == "text":
    # Logic: Text input is tricky in Streamlit loops. We use st.chat_input.
    
    # Check for "Skip" option
    if current_step.get("optional"):
        if st.button("Skip this step", key=f"skip_{current_step['id']}"):
            advance_step("Skipped", current_step['id'], "None")

    user_text = st.chat_input("Type your answer here...")
    
    if user_text:
        # Validate logic
        is_valid, error_msg = validate_with_ai(current_step['id'], user_text)
        
        if is_valid:
            advance_step(user_text, current_step['id'], user_text)
        else:
            st.error(f"🚫 {error_msg}")
