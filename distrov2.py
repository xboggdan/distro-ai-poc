import streamlit as st
import openai
import google.generativeai as genai
import json
import os

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(page_title="DistroPro AI", layout="wide")

# Retrieve Keys
openai_key = st.secrets.get("OPENAI_API_KEY")
gemini_key = st.secrets.get("GEMINI_API_KEY")
groq_key = st.secrets.get("GROQ_API_KEY")

if gemini_key:
    genai.configure(api_key=gemini_key)

# --- 2. THE STRICT RULE ENGINE (STATE MACHINE) ---
# This dictionary DEFINES your exact steps. Edit the text here to change the rules.
WORKFLOW_STEPS = {
    1: {
        "name": "Artist Name",
        "system_instruction": "You are a Music Distributor. Your ONLY goal right now is to ask the user for their Artist Name. Do not ask for anything else. Keep it short.",
        "extraction_prompt": "Extract the Artist Name from the user's text. Return ONLY the name. If they didn't provide a name, return 'None'."
    },
    2: {
        "name": "Track Title",
        "system_instruction": "You have the artist name. Now, your ONLY goal is to ask for the Track Title. Do not ask about genre yet.",
        "extraction_prompt": "Extract the Track Title from the user's text. Return ONLY the title. If invalid, return 'None'."
    },
    3: {
        "name": "Genre Selection",
        "system_instruction": "Now ask for the Genre of the track (e.g., Pop, Hip-Hop, Electronic). Offer 3 popular examples.",
        "extraction_prompt": "Extract the Genre from the text. Return ONLY the genre."
    },
    4: {
        "name": "Confirmation",
        "system_instruction": "Summarize the data: Artist, Track, and Genre. Ask the user to type 'Yes' to confirm or 'No' to restart.",
        "extraction_prompt": "Did the user say 'Yes' or confirm? Return 'CONFIRMED' if yes, otherwise 'FALSE'."
    }
}

# --- 3. SESSION STATE INITIALIZATION ---
# This acts as the "Memory" of the application
if "current_step" not in st.session_state:
    st.session_state.current_step = 0 # 0 = Not started
if "collected_data" not in st.session_state:
    st.session_state.collected_data = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- 4. ADVANCED AI BACKEND (GROQ PRIORITY) ---
def query_llm(system_prompt, user_text):
    """
    Sends a request to Groq (Priority) -> OpenAI -> Gemini.
    Returns just the text response.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text}
    ]

    # OPTION A: GROQ (Fastest/Free)
    if groq_key:
        try:
            client = openai.OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
            resp = client.chat.completions.create(model="llama-3.1-8b-instant", messages=messages)
            return resp.choices[0].message.content, "Groq"
        except Exception as e:
            print(f"Groq failed: {e}")

    # OPTION B: OPENAI (Reliable)
    if openai_key:
        try:
            client = openai.OpenAI(api_key=openai_key)
            resp = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages)
            return resp.choices[0].message.content, "OpenAI"
        except Exception:
            pass

    # OPTION C: GEMINI (Backup)
    if gemini_key:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            full_prompt = f"SYSTEM: {system_prompt}\nUSER: {user_text}"
            resp = model.generate_content(full_prompt)
            return resp.text, "Gemini"
        except Exception:
            pass

    return "Error: All AI services failed.", "Error"

# --- 5. MAIN LOGIC LOOP ---

st.title("🚀 DistroBot Pro")

# Sidebar Progress
if st.session_state.current_step > 0:
    progress_val = (st.session_state.current_step - 1) / len(WORKFLOW_STEPS)
    st.progress(progress_val)
    st.sidebar.write(f"**Current Step:** {st.session_state.current_step}/{len(WORKFLOW_STEPS)}")
    st.sidebar.json(st.session_state.collected_data) # Debug view of data

# Display Chat History
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- CORE STATE MACHINE ENGINE ---
user_input = st.chat_input("Type your message...")

if user_input:
    # 1. Show User Message
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # 2. START THE WORKFLOW (If step 0)
    if st.session_state.current_step == 0:
        st.session_state.current_step = 1
        # We don't extract data on step 0, we just trigger the welcome.
        step_config = WORKFLOW_STEPS[1]
        
        # Ask the AI to generate the first question based on the rule
        ai_response, provider = query_llm(step_config["system_instruction"], "Introduce yourself and start the process.")
        
        with st.chat_message("assistant"):
            st.write(ai_response)
            st.caption(f"⚡ powered by {provider}")
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})

    # 3. PROCESS STEPS (If step > 0)
    else:
        current_step_num = st.session_state.current_step
        step_config = WORKFLOW_STEPS[current_step_num]

        # A. EXTRACT DATA from the user's input using the AI
        extraction_instruction = step_config["extraction_prompt"]
        extracted_data, _ = query_llm(extraction_instruction, user_input)
        
        # Clean up the extracted text (remove quotes, whitespace)
        cleaned_data = extracted_data.strip().replace('"', '').replace("'", "")

        # Logic Check: Did we get valid data?
        if "None" in cleaned_data or len(cleaned_data) < 2:
            # FAILURE: User typed nonsense. Don't advance step.
            error_msg = "I didn't quite catch that. Could you please clarify?"
            with st.chat_message("assistant"):
                st.write(error_msg)
            st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
        
        else:
            # SUCCESS: Save data and Move to Next Step
            st.session_state.collected_data[step_config["name"]] = cleaned_data
            
            # Check if workflow is finished
            if current_step_num >= len(WORKFLOW_STEPS):
                st.balloons()
                final_msg = f"Great! I have registered: {st.session_state.collected_data}. Process Complete."
                with st.chat_message("assistant"):
                    st.success(final_msg)
                st.session_state.chat_history.append({"role": "assistant", "content": final_msg})
                # Optional: Reset
                # st.session_state.current_step = 0
            else:
                # Advance Step
                st.session_state.current_step += 1
                next_step_num = st.session_state.current_step
                next_config = WORKFLOW_STEPS[next_step_num]
                
                # Generate Question for the NEXT step
                context_str = f"Current Data: {st.session_state.collected_data}. User just said: {user_input}"
                ai_response, provider = query_llm(next_config["system_instruction"], context_str)
                
                with st.chat_message("assistant"):
                    st.write(ai_response)
                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})

# Reset Button
if st.sidebar.button("Restart"):
    st.session_state.current_step = 0
    st.session_state.collected_data = {}
    st.session_state.chat_history = []
    st.rerun()
