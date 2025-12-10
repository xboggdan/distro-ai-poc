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

# --- 2. OFFICIAL POLICY DOCUMENTATION ---
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
- Words 1 -> Special Characters including emojis not allowed here: \/!@#$%^&*+= (Note: Brackets (){}[] ARE allowed).
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
- Requirement: Must be at least two names (First and Last).
Validation Message: Provide a legal first and last name (e.g. John Doe).

ID 9: Track Title (Mandatory)
Field Validations:
- Forbidden_Words #1: feat., featuring, produced, prod.
- Forbidden_Words #2: Acoustic, Remastered, Freestyle, Instrumental, remixed, remix
- Brackets are allowed.
"""

# --- 3. THE VALIDATION ENGINE ---

class DistroBotStateMachine:
    def __init__(self):
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
                "error_msg": "Validation Error: Composer must be a real name (First Last). No 'music', 'beats', or special characters."
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
    Robust JSON cleaner that handles Markdown blocks and extra text.
    """
    if not raw_text: return None
    try:
        # Remove markdown code blocks if present (e.g. ```json ... ```)
        clean_text = raw_text.replace("```json", "").replace("```", "").strip()
        
        # Try finding the first JSON object
        match = re.search(r'\{.*\}', clean_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(clean_text)
    except Exception as e:
        st.error(f"Debug Info: JSON Parse failed. AI Output: {raw_text}")
        return None

def query_llm_for_validation(field_name, doc_id, user_input):
    """
    Uses JSON Mode to strictly enforce structured output.
    """
    system_prompt = f"""
    You are a QC Logic Engine.
    
    POLICY:
    {OFFICIAL_POLICY_DOC}
    
    TASK:
    Analyze input: "{user_input}"
    Check against Field "{field_name}" (Ref: {doc_id}).
    
    STRICT RULES:
    - If Field is 'Composer', REJECT if it is only one word. It must be First and Last name.
    - Check for forbidden characters and words.
    
    OUTPUT FORMAT:
    You must output a valid JSON object.
    {{
        "value": "Cleaned Input",
        "valid": true/false,
        "reason": "Short reason if invalid"
    }}
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    
    extracted_text = None
    
    # 1. TRY GROQ (With JSON Mode)
    if groq_key:
        try:
            client = openai.OpenAI(base_url="[https://api.groq.com/openai/v1](https://api.groq.com/openai/v1)", api_key=groq_key)
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant", 
                messages=messages,
                temperature=0,
                response_format={"type": "json_object"}  # <--- THE FIX
            )
            extracted_text = resp.choices[0].message.content
        except Exception as e:
            # st.error(f"Groq Error: {e}") # Uncomment to debug
            pass

    # 2. FALLBACK TO GEMINI (Text Mode)
    if not extracted_text and gemini_key:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            extracted_text = model.generate_content(system_prompt).text
        except: pass

    return clean_json_response(extracted_text)

# --- 5. MAIN APP LOGIC ---

if "fsm" not in st.session_state:
    st.session_state.fsm = DistroBotStateMachine()
if "current_step" not in st.session_state:
    st.session_state.current_step = 1
if "collected_data" not in st.session_state:
    st.session_state.collected_data = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# UI Layout
st.title("🛡️ Distro QC Bot (Fixed)")
col1, col2 = st.columns([2, 1])

# Sidebar: Debug View
with col2:
    st.subheader("QC Status")
    st.json(st.session_state.collected_data)
    if st.button("Reset Wizard"):
        st.session_state.current_step = 1
        st.session_state.collected_data = {}
        st.session_state.chat_history = []
        st.rerun()

# Chat Area
with col1:
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if len(st.session_state.chat_history) == 0:
        first_config = st.session_state.fsm.get_current_config(1)
        st.session_state.chat_history.append({"role": "assistant", "content": first_config["prompt"]})
        st.rerun()

    if user_input := st.chat_input("Enter details..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        step_idx = st.session_state.current_step
        step_config = st.session_state.fsm.get_current_config(step_idx)

        if step_idx <= 4:
            with st.spinner("Validating..."):
                qc_result = query_llm_for_validation(
                    step_config["field"], 
                    step_config["doc_id"], 
                    user_input
                )

            if qc_result and qc_result.get("valid") == True:
                st.session_state.collected_data[step_config["field"]] = qc_result.get("value")
                st.session_state.current_step += 1
                next_step = st.session_state.fsm.get_current_config(st.session_state.current_step)
                bot_reply = next_step["prompt"] if next_step else "Validation Complete. Type 'Yes' to finalize."
            else:
                reason = qc_result.get("reason", "Formatting Error") if qc_result else "System Error (JSON Parsing)."
                bot_reply = f"🚫 **Rejected:** {reason}\n\n*Reference: {step_config['doc_id']}*"

        elif step_idx == 5:
            if "yes" in user_input.lower():
                bot_reply = "✅ Submitted to Distribution Queue."
                st.balloons()
            else:
                bot_reply = "❌ Submission Aborted."

        st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
        with st.chat_message("assistant"):
            st.markdown(bot_reply)
        st.rerun()
