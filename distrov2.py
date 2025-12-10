import streamlit as st
import openai
import google.generativeai as genai
import json
import re
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="DistroPro AI", layout="wide")

# Retrieve Keys
openai_key = st.secrets.get("OPENAI_API_KEY")
gemini_key = st.secrets.get("GEMINI_API_KEY")
groq_key = st.secrets.get("GROQ_API_KEY")

if gemini_key:
    genai.configure(api_key=gemini_key)

# --- 2. BUSINESS LOGIC (YOUR CONFLUENCE RULES) ---
# PASTE YOUR FULL DOCS HERE. The bot will use this as its "Bible".
CONFLUENCE_RULES = """
1. ARTIST NAME VALIDATION:
   - Must be a real name, not a sentence like "I don't know".
   - If unclear, ask for clarification.

2. TRACK TITLE VALIDATION:
   - Must not be empty.
   - If the user types "Untitled", confirm if that is the actual title.

3. GENRE VALIDATION:
   - Must be a standard music genre (Pop, Hip-Hop, Rock, Electronic, Jazz, Classical).
   - If the user describes a mood (e.g., "sad song"), suggest a genre but DO NOT accept the mood as the genre.

4. STEP ORDER:
   - You MUST collect Artist Name first.
   - You MUST collect Track Title second.
   - You MUST collect Genre third.
   - You CANNOT proceed to the next step until the current data is valid.
"""

# --- 3. THE VALIDATION ENGINE ---

class DistroBotStateMachine:
    def __init__(self):
        # Define the exact steps and their strict requirements
        self.steps = {
            1: {
                "field": "Artist Name",
                "prompt": "Ask the user for their Artist Name.",
                "error_msg": "That doesn't look like a valid artist name. Please try again."
            },
            2: {
                "field": "Track Title",
                "prompt": "Ask for the Track Title.",
                "error_msg": "Please provide a valid track title."
            },
            3: {
                "field": "Genre",
                "prompt": "Ask for the Genre (e.g., Pop, Hip Hop, Rock).",
                "error_msg": "I didn't recognize that genre. Please choose a standard genre."
            },
            4: {
                "field": "Confirmation",
                "prompt": "Show the collected data and ask for 'Yes' to confirm.",
                "error_msg": "Please type 'Yes' to confirm or 'No' to restart."
            }
        }

    def get_current_config(self, step_number):
        return self.steps.get(step_number)

# --- 4. HELPER FUNCTIONS ---

def clean_json_response(raw_text):
    """
    CRITICAL: Strips out 'Here is the JSON' or 'I found this' text 
    and returns ONLY the valid JSON string.
    """
    try:
        # Regex to find the first { and the last }
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            # Fallback: try to parse the whole text if regex fails
            return json.loads(raw_text)
    except Exception as e:
        print(f"JSON Parse Error: {e} | Raw Text: {raw_text}")
        return None

def query_llm_for_extraction(field_name, user_input, history_context):
    """
    Asks the AI to extract data in STRICT JSON format.
    """
    system_prompt = f"""
    You are a Data Extraction Engine.
    RULES:
    1. Analyze the user's input: "{user_input}"
    2. Extract the value for the field: "{field_name}"
    3. Use the Context Rules: {CONFLUENCE_RULES}
    4. RETURN ONLY JSON. No text, no explanations.
    5. Format: {{"value": "extracted_data", "valid": true/false}}
    6. If the user input is off-topic or invalid according to the rules, set "valid": false.
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
                temperature=0 # Zero temperature for strict logic
            )
            extracted_text = resp.choices[0].message.content
        except: pass

    elif gemini_key:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            extracted_text = model.generate_content(system_prompt).text
        except: pass

    # Clean the response
    return clean_json_response(extracted_text)

def generate_bot_response(step_prompt, context_data):
    """Generates the conversational reply for the bot."""
    system = f"""
    You are DistroBot. {CONFLUENCE_RULES}
    Current Goal: {step_prompt}
    Context so far: {context_data}
    Keep it professional and short.
    """
    # Use Groq or others to generate the chat text
    if groq_key:
        client = openai.OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
        resp = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "system", "content": system}])
        return resp.choices[0].message.content
    return "Please continue."

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
st.title("🎹 DistroBot: Strict Mode")
col1, col2 = st.columns([2, 1])

# Sidebar: Debug View (So you can see what the bot captures)
with col2:
    st.subheader("📝 Live Data State")
    st.json(st.session_state.collected_data)
    st.write(f"**Current Step:** {st.session_state.current_step}")
    if st.button("Reset Process"):
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
        first_msg = "Hello! I am ready to start your release. What is your Artist Name?"
        st.session_state.chat_history.append({"role": "assistant", "content": first_msg})
        st.rerun()

    # User Input
    if user_input := st.chat_input("Type here..."):
        # 1. Display User Message
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 2. Identify Current Step & Requirements
        step_idx = st.session_state.current_step
        step_config = st.session_state.fsm.get_current_config(step_idx)

        # 3. EXTRACTION PHASE (The Strict Part)
        if step_idx <= 3: # Extraction Steps
            with st.spinner("Validating..."):
                extraction_result = query_llm_for_extraction(
                    step_config["field"], 
                    user_input, 
                    st.session_state.collected_data
                )

            # 4. VALIDATION GATE
            if extraction_result and extraction_result.get("valid") == True:
                # Success: Save data and move forward
                value = extraction_result.get("value")
                st.session_state.collected_data[step_config["field"]] = value
                
                # Advance Step
                st.session_state.current_step += 1
                next_step_config = st.session_state.fsm.get_current_config(st.session_state.current_step)
                
                if next_step_config:
                    # Generate question for NEXT step
                    bot_reply = generate_bot_response(next_step_config["prompt"], st.session_state.collected_data)
                else:
                    # Workflow Finished
                    bot_reply = "Process Complete! Please type 'Yes' to submit."
            
            else:
                # Failure: Stay on same step, complain to user
                bot_reply = step_config["error_msg"]

        elif step_idx == 4: # Confirmation Step
            if "yes" in user_input.lower():
                bot_reply = "✅ Release Submitted successfully!"
                st.balloons()
            else:
                bot_reply = "❌ Release Cancelled. Click Reset to start over."

        # 5. Display Bot Response
        st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
        with st.chat_message("assistant"):
            st.markdown(bot_reply)
        
        st.rerun()
