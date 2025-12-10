import streamlit as st
import openai
import google.generativeai as genai
import json
import re
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="DistroPro QC Engine", layout="wide")

# Retrieve Keys
openai_key = st.secrets.get("OPENAI_API_KEY")
gemini_key = st.secrets.get("GEMINI_API_KEY")
groq_key = st.secrets.get("GROQ_API_KEY")

if gemini_key:
    genai.configure(api_key=gemini_key)

# --- 2. OFFICIAL POLICY DOCUMENTATION (RAW SOURCE) ---
# This contains the specific validations, forbidden words, and ID references.
OFFICIAL_POLICY_DOC = """
I. Background 
The goal is to facilitate healthier and more accurate submissions, significantly reducing the likelihood of rejection by our QC team.

II. Document Purpose. 
4. Detail the validation restrictions, including a list of forbidden words, for each field 

III. Emojis should not be allowed in any distribution field 

III.a Fields & Validations 1st Wizard Step

ID 1: Release Title (Mandatory)
Field Validations:
- if the user inputs specific words within parentheses and/or brackets, we throw an exception.
- Forbidden_Words #1: feat., featuring, produced, prod., feat, ft,ft.
- Forbidden_Words #2: Acoustic, Remastered, Freestyle, Instrumental, remixed, remix
- Words 1 -> Special Characters including emojis not allowed here: \/!@#$%^&*+= (Note: Brackets (){}[] ARE allowed, per Justin Sullivan's update).
Validation Message: Please avoid restricted words like feat, prod, remix.

ID 2: Version (Optional)
Field Validations:
- Words 1 -> Special Characters not allowed here: (){}[]\/!@#$%^&*+=
- Words 2 -> Additional forbidden words: new, featuring, feat, feat., ft, ft., Official, Explicit.

ID 3: Primary Artist (Mandatory)
Field Validations:
- Words #1: feat., featuring, produced, prod., feat, ft,ft.
- Words #2: Acoustic, Remastered, Freestyle, Instrumental, remixed
We trigger the validation errors only when one or more of the above words have been filled inside brackets.
Validation Message: Please input contributors in the contributors field.

ID 5: Genre (Mandatory)
Bottom Sheet: Choose only one primary genre that best represents your release.

ID 11: Composer (Mandatory)
Description: First and last name of the Artist. Ideally legal name.
Field Validations:
- Special Characters not allowed here: (){}[]\/!@#$%^&*+=
- Forbidden Words: music, beats (automatic rejection from Fuga).
Validation Message: Provide a legal first and last name.

ID 9: Track Title (Mandatory)
Field Validations:
- Forbidden_Words #1: feat., featuring, produced, prod.
- Forbidden_Words #2: Acoustic, Remastered, Freestyle, Instrumental, remixed, remix
- Brackets are allowed.

JUSTIN SULLIVAN UPDATE (Override):
- Allow brackets in the title since it may be used as a secondary title (), [], {}.
- Allow special characters in contributors names.
- Keep validation strictly for composers and lyricists (No special chars).
"""

# --- 3. THE VALIDATION ENGINE ---

class DistroBotStateMachine:
    def __init__(self):
        # We map the steps to the specific ID in the documentation
        self.steps = {
            1: {
                "field": "Release Title",
                "doc_id": "ID 1",
                "prompt": "What is the Title of your release?",
                "error_msg": "Validation Error: Title contains forbidden words (feat, prod) or illegal characters."
            },
            2: {
                "field": "Primary Artist",
                "doc_id": "ID 3",
                "prompt": "Great. What is the Primary Artist Name?",
                "error_msg": "Validation Error: Artist name cannot contain 'feat', 'prod' or brackets with roles."
            },
            3: {
                "field": "Genre",
                "doc_id": "ID 5",
                "prompt": "Select the Genre (e.g., Pop, Hip Hop, Rock).",
                "error_msg": "Please select a valid standard genre."
            },
            4: {
                "field": "Composer",
                "doc_id": "ID 11",
                "prompt": "Who is the Composer? (Legal First & Last Name required).",
                "error_msg": "Validation Error: Composer must be a real name. No 'music', 'beats', or special characters allowed."
            },
            5: {
                "field": "Confirmation",
                "doc_id": "Final",
                "prompt": "Review the data above. Type 'Yes' to submit to QC.",
                "error_msg": "Type 'Yes' to confirm."
            }
        }

    def get_current_config(self, step_number):
        return self.steps.get(step_number)

# --- 4. HELPER FUNCTIONS ---

def clean_json_response(raw_text):
    """
    Strips out conversational text and returns ONLY the valid JSON string.
    """
    try:
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(raw_text)
    except Exception:
        return None

def query_llm_for_validation(field_name, doc_id, user_input):
    """
    Asks the AI to validate the input against the OFFICIAL_POLICY_DOC.
    """
    system_prompt = f"""
    You are a Music Distribution Quality Control (QC) Engine.
    
    YOUR KNOWLEDGE BASE (The Policy):
    {OFFICIAL_POLICY_DOC}
    
    TASK:
    1. Analyze the user's input: "{user_input}"
    2. Check it against the rules for Field "{field_name}" (Reference {doc_id} in the Policy).
    3. Check for Global Rules (No Emojis).
    4. Check for Specific Forbidden Words listed in the Policy for this ID.
    
    OUTPUT FORMAT (JSON ONLY):
    {{
        "value": "Cleaned Version of Input (Capitalize first letters)",
        "valid": true or false,
        "reason": "If false, quote the specific rule violated from the Policy"
    }}
    """
    
    # Priority: Groq -> OpenAI -> Gemini
    messages = [{"role": "system", "content": system_prompt}]
    
    extracted_text = "Error"
    
    if groq_key:
        try:
            client = openai.OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant", 
                messages=messages,
                temperature=0 # Strict logic
            )
            extracted_text = resp.choices[0].message.content
        except: pass

    elif gemini_key:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            extracted_text = model.generate_content(system_prompt).text
        except: pass

    return clean_json_response(extracted_text)

# --- 5. MAIN APP LOGIC ---

# Initialize State
if "fsm" not in st.session_state:
    st.session_state.fsm = DistroBotStateMachine()
if "current_step" not in st.session_state:
    st.session_state.current_step = 1
if "collected_data" not in st.session_state:
    st.session_state.collected_data = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# UI Layout
st.title("🛡️ Distro QC Bot (Strict Mode)")
col1, col2 = st.columns([2, 1])

# Sidebar: Debug View
with col2:
    st.subheader("QC Status")
    st.json(st.session_state.collected_data)
    st.write(f"**Wizard Step:** {st.session_state.current_step}")
    if st.button("Reset Wizard"):
        st.session_state.current_step = 1
        st.session_state.collected_data = {}
        st.session_state.chat_history = []
        st.rerun()

# Chat Area
with col1:
    # Display History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Initial Greeting
    if len(st.session_state.chat_history) == 0:
        first_config = st.session_state.fsm.get_current_config(1)
        st.session_state.chat_history.append({"role": "assistant", "content": first_config["prompt"]})
        st.rerun()

    # User Input
    if user_input := st.chat_input("Enter details..."):
        # 1. Display User Message
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 2. Identify Current Step
        step_idx = st.session_state.current_step
        step_config = st.session_state.fsm.get_current_config(step_idx)

        # 3. VALIDATION PHASE
        if step_idx <= 4: # Validation Steps
            with st.spinner(f"Checking '{step_config['field']}' against Policy {step_config['doc_id']}..."):
                qc_result = query_llm_for_validation(
                    step_config["field"], 
                    step_config["doc_id"], 
                    user_input
                )

            # 4. DECISION GATE
            if qc_result and qc_result.get("valid") == True:
                # Success
                value = qc_result.get("value")
                st.session_state.collected_data[step_config["field"]] = value
                
                # Advance
                st.session_state.current_step += 1
                next_step = st.session_state.fsm.get_current_config(st.session_state.current_step)
                
                if next_step:
                    bot_reply = next_step["prompt"]
                else:
                    bot_reply = "Validation Complete. Type 'Yes' to finalize."
            
            else:
                # Failure (Show the specific policy reason)
                reason = qc_result.get("reason", "Unknown policy violation") if qc_result else "Invalid format."
                bot_reply = f"🚫 **Rejected:** {reason}\n\n*Reference: {step_config['doc_id']}*"

        elif step_idx == 5: # Confirmation
            if "yes" in user_input.lower():
                bot_reply = "✅ Submitted to Distribution Queue."
                st.balloons()
            else:
                bot_reply = "❌ Submission Aborted."

        # 5. Output
        st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
        with st.chat_message("assistant"):
            st.markdown(bot_reply)
        
        st.rerun()
