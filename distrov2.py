import streamlit as st
import time
import re
import random

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="BandLab Distribution Flow", layout="wide", page_icon="🎸")

# BandLab Custom CSS (Red & Black Theme)
st.markdown("""
<style>
    /* Main Buttons */
    .stButton>button {
        background-color: #F04238;
        color: white;
        border-radius: 20px;
        font-weight: bold;
        border: none;
    }
    /* Wizard Chat Bubbles (Left) */
    .wizard-msg {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #F04238;
    }
    /* Mentor Chat Bubbles (Right) */
    .mentor-msg {
        background-color: #e8f4f9;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #2C3E50;
    }
    /* Headers */
    h1 { color: #F04238; }
</style>
""", unsafe_allow_html=True)

# --- 2. THE RULEBOOK (Strict Validation Logic) ---
# Derived strictly from your "Field Restrictions & Guidelines" document

STRICT_RULES = {
    "title": {
        "forbidden": ["feat.", "featuring", "produced", "prod.", "ft.", "ft", "remix", "acoustic"],
        "special_chars": r"[\(\)\{\}\[\]\\\/!@#$%\^&\*\+=]",
        "error_forbidden": "❌ **Policy:** 'Feat', 'Prod', or 'Remix' are not allowed in the Title field. Please use the Version or Contributor fields.",
        "error_chars": "❌ **Policy:** Special characters (brackets, symbols) are not allowed in the Release Title."
    },
    "version": {
        "forbidden": ["new", "official", "explicit", "feat", "ft"],
        "special_chars": r"[\(\)\{\}\[\]\\\/!@#$%\^&\*\+=]",
        "error_forbidden": "❌ **Policy:** Do not use words like 'New', 'Official', or 'Feat' in the Version field.",
    },
    "composer": {
        "forbidden": ["music", "beats", "prod", "productions"],
        "special_chars": r"[!@#$%\^&\*\+=]",
        "min_words": 2,
        "error_forbidden": "❌ **Rejection Risk:** 'Music', 'Beats', or 'Prod' are not valid legal names.",
        "error_format": "❌ **Policy:** Stores require a Legal First & Last Name (e.g., 'John Doe') for royalties."
    },
    "upc": {
        "regex": r"^\d{12}$",
        "error_format": "❌ **Format:** UPC must be exactly 12 numbers."
    }
}

# --- 3. SESSION STATE INITIALIZATION ---
if "wizard_history" not in st.session_state:
    st.session_state.wizard_history = [
        {"role": "assistant", "content": "Let's get your **Single** ready for Spotify.\n\n**Step 1:** Please upload your **Audio File**."}
    ]
if "mentor_history" not in st.session_state:
    st.session_state.mentor_history = [
        {"role": "assistant", "content": "👋 I'm your **Guide**. Ask me questions like *'What is a UPC?'* or *'Why do I need a legal name?'* and I'll answer here so you don't lose your place."}
    ]
if "step" not in st.session_state:
    st.session_state.step = "upload" # Steps: upload -> title -> version -> artist -> genre -> composer -> upc -> review
if "data" not in st.session_state:
    st.session_state.data = {}

# --- 4. THE BRAIN: INTENT & VALIDATION ---

def check_intent(text):
    """
    Decides if user is providing Data or Asking a Question.
    """
    question_triggers = ["what is", "why", "how to", "explain", "help", "mean", "?"]
    text_lower = text.lower()
    
    if any(trigger in text_lower for trigger in question_triggers):
        return "QUESTION"
    return "DATA"

def validate(step, text):
    """
    Runs text against the STRICT_RULES dictionary.
    """
    rules = STRICT_RULES.get(step)
    if not rules:
        return None # No strict rules for this step (e.g. Genre)

    text_lower = text.lower()

    # 1. Check Forbidden Words
    if "forbidden" in rules:
        if any(w in text_lower for w in rules["forbidden"]):
            return rules["error_forbidden"]
            
    # 2. Check Special Characters
    if "special_chars" in rules:
        if re.search(rules["special_chars"], text):
            return rules.get("error_chars", "❌ Special characters are not allowed.")

    # 3. Check Word Count (for Names)
    if "min_words" in rules:
        if len(text.split()) < rules["min_words"]:
            return rules.get("error_format", "Invalid format.")

    # 4. Regex (for UPC)
    if "regex" in rules:
        if not re.match(rules["regex"], text) and text_lower != "skip":
            return rules["error_format"]

    return None # Validation Passed

def get_mentor_answer(question):
    """
    Simulated Knowledge Base (RAG)
    """
    q = question.lower()
    if "upc" in q: return "💡 **UPC** stands for Universal Product Code. It identifies your *entire release*. If you don't have one, just type 'skip' and BandLab generates it for free."
    if "isrc" in q: return "💡 **ISRC** tracks a single song. We create this for you automatically."
    if "legal" in q or "name" in q: return "💡 **Why Legal Names?**\nPerformance Rights Organizations (PROs) need real names to ensure royalties go to the right person, not a stage alias."
    if "feat" in q: return "💡 **Featuring Artists:** Stores require featured artists to be listed in a specific field, not in the song title, to ensure clickable artist links."
    if "version" in q: return "💡 **Version:** Use this for 'Radio Edit', 'Remix', or 'Live'. Leave it blank for the original song."
    
    return "💡 That's a great question. You can usually find the answer in our Help Center, but for now, let's focus on the release!"

# --- 5. UI LAYOUT ---

st.title("🚀 BandLab Distribution Assistant")
st.markdown("---")

# THE DUAL COLUMN LAYOUT
col_wizard, col_spacer, col_mentor = st.columns([5, 0.5, 3])

# --- LEFT COLUMN: THE WIZARD (Action) ---
with col_wizard:
    st.subheader("📝 Release Wizard")
    
    # Render Wizard History
    for msg in st.session_state.wizard_history:
        if msg["role"] == "assistant":
            st.markdown(f'<div class="wizard-msg"><b>Assistant:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="text-align: right; margin-bottom: 10px; color: #666;">You: {msg["content"]}</div>', unsafe_allow_html=True)

    # Special Widget for Upload Step
    if st.session_state.step == "upload":
        uploaded = st.file_uploader("Select Audio File (WAV/MP3)", key="audio_up")
        if uploaded:
            st.session_state.wizard_history.append({"role": "user", "content": "Audio uploaded."})
            st.session_state.wizard_history.append({"role": "assistant", "content": "Audio received! 🎵\n\n**Step 2:** What is the **Release Title**? (e.g. 'Midnight Rain')"})
            st.session_state.step = "title"
            st.rerun()

# --- RIGHT COLUMN: THE MENTOR (Context) ---
with col_mentor:
    st.subheader("🧠 Knowledge Base")
    st.info("I am listening to your conversation. If you ask a question, I will answer here.")
    
    # Render Mentor History
    for msg in st.session_state.mentor_history:
        st.markdown(f'<div class="mentor-msg">{msg["content"]}</div>', unsafe_allow_html=True)

# --- BOTTOM: UNIFIED INPUT BAR ---
st.markdown("---")
user_input = st.chat_input("Type your answer OR ask a question here...")

if user_input:
    
    # 1. DECIDE INTENT
    intent = check_intent(user_input)
    
    if intent == "QUESTION":
        # -> Route to Right Column (Mentor)
        answer = get_mentor_answer(user_input)
        st.session_state.mentor_history.append({"role": "assistant", "content": f"**You asked:** {user_input}\n\n{answer}"})
        st.rerun()
        
    else:
        # -> Route to Left Column (Wizard)
        st.session_state.wizard_history.append({"role": "user", "content": user_input})
        
        # 2. VALIDATE DATA
        error = validate(st.session_state.step, user_input)
        
        if error:
            # Validation Failed
            st.session_state.wizard_history.append({"role": "assistant", "content": error})
        else:
            # Validation Passed - Advance Step
            if st.session_state.step == "title":
                st.session_state.data["title"] = user_input
                st.session_state.wizard_history.append({"role": "assistant", "content": f"✅ Title '**{user_input}**' saved.\n\n**Step 3:** What is the **Version**? (Type 'Original' or 'skip' if none)."})
                st.session_state.step = "version"
            
            elif st.session_state.step == "version":
                val = user_input if user_input.lower() != "skip" else "Original"
                st.session_state.data["version"] = val
                st.session_state.wizard_history.append({"role": "assistant", "content": f"✅ Version set to '{val}'.\n\n**Step 4:** Who is the **Main Artist**?"})
                st.session_state.step = "artist"

            elif st.session_state.step == "artist":
                st.session_state.data["artist"] = user_input
                st.session_state.wizard_history.append({"role": "assistant", "content": f"✅ Artist saved.\n\n**Step 5:** What is the **Genre**?"})
                st.session_state.step = "genre"

            elif st.session_state.step == "genre":
                st.session_state.data["genre"] = user_input
                st.session_state.wizard_history.append({"role": "assistant", "content": f"✅ Genre saved.\n\n**Step 6:** What is the **Composer's Legal Name**? (First & Last required)."})
                st.session_state.step = "composer"
            
            elif st.session_state.step == "composer":
                st.session_state.data["composer"] = user_input
                st.session_state.wizard_history.append({"role": "assistant", "content": f"✅ Composer info locked.\n\n**Step 7:** Enter 12-digit **UPC** (or type 'skip' to auto-generate)."})
                st.session_state.step = "upc"
            
            elif st.session_state.step == "upc":
                upc_val = user_input if user_input.lower() != "skip" else "Auto-Generated"
                st.session_state.data["upc"] = upc_val
                st.session_state.step = "review"
                
                # FINAL SUMMARY
                summary = f"""
                🎉 **Release Ready for Submission!**
                
                **Title:** {st.session_state.data.get('title')}
                **Version:** {st.session_state.data.get('version')}
                **Artist:** {st.session_state.data.get('artist')}
                **Genre:** {st.session_state.data.get('genre')}
                **Composer:** {st.session_state.data.get('composer')}
                **UPC:** {st.session_state.data.get('upc')}
                """
                st.session_state.wizard_history.append({"role": "assistant", "content": summary})
        
        st.rerun()