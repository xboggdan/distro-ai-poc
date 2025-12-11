import streamlit as st
import time
import random

# --- CONFIGURATION ---
st.set_page_config(page_title="DistroBot V9", page_icon="💿", layout="wide")

# --- CSS FOR "WAY BETTER UI" ---
st.markdown("""
<style>
    .stChatMessage {
        background-color: #f9f9f9;
        border-radius: 15px;
        padding: 10px;
        border: 1px solid #eee;
    }
    .stButton button {
        border-radius: 20px;
        font-weight: bold;
    }
    /* Fix for chat input visibility */
    .stChatInput {
        position: fixed;
        bottom: 0;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I'm DistroBot V9. Let's get your music on Spotify and Apple Music. What is the **Release Title**?"}]
if "step" not in st.session_state:
    st.session_state.step = "title"  # title, version, artist, genre, cover_art, cover_fix, audio, contributors, summary
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "mode" not in st.session_state:
    st.session_state.mode = "Distribution Flow"

# --- HELPER FUNCTIONS ---

def simulate_ai_extraction(user_input, field_type):
    """
    Simulates 'Smart AI' that extracts entities from conversational sentences.
    In a real scenario, this would call your agent_api.py/OpenAI.
    """
    triggers = ["my title is", "the title is", "it's called", "name is", "release title is"]
    cleaned = user_input
    
    # Simple rule-based extraction to demonstrate logic
    lower_input = user_input.lower()
    for trigger in triggers:
        if trigger in lower_input:
            # Split and take the part after the trigger
            start_index = lower_input.find(trigger) + len(trigger)
            cleaned = user_input[start_index:].strip()
            # Remove common punctuation at ends
            cleaned = cleaned.strip('".')
            return cleaned
    
    return user_input.strip()

def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})

# --- SIDEBAR: SETTINGS & EDITING ---
with st.sidebar:
    st.title("🎛 Control Center")
    
    # Mode Toggle
    mode = st.radio("Interaction Mode", ["Distribution Flow", "Educational / Help"], index=0 if st.session_state.mode == "Distribution Flow" else 1)
    if mode != st.session_state.mode:
        st.session_state.mode = mode
        st.rerun()

    st.divider()

    # README (Expanded by default as requested)
    with st.expander("📖 README & Architecture", expanded=True):
        st.markdown("""
        **DistroBot V9 Architecture**
        - **Core:** Python (Streamlit)
        - **Logic:** State Machine for Metadata
        - **Models:** Connected to `list_models.py`
        
        **How it works:**
        1. AI extracts entities from natural language.
        2. Strict validation for DSP compliance.
        3. Automated Asset Checks (ACR/Vision).
        """)

    # Edit Past Answers (New Feature)
    if st.session_state.mode == "Distribution Flow" and st.session_state.user_data:
        with st.expander("✏️ Edit Metadata", expanded=False):
            st.write("Need to change something?")
            for key, value in st.session_state.user_data.items():
                new_val = st.text_input(f"Edit {key}", value)
                if new_val != value:
                    st.session_state.user_data[key] = new_val
                    st.success(f"Updated {key}!")

    if st.button("Reset Session"):
        st.session_state.clear()
        st.rerun()

# --- MAIN APP LOGIC ---

# 1. Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 2. EDUCATIONAL MODE
if st.session_state.mode == "Educational / Help":
    user_input = st.chat_input("Ask me anything about music distribution...")
    if user_input:
        add_message("user", user_input)
        with st.chat_message("user"):
            st.write(user_input)
        
        # Mock Response Logic for Education
        response = "I can help with that! According to BandLab Terms and FAQ, you keep 100% of your rights. "
        if "royalties" in user_input.lower():
            response += "Royalties are paid out monthly via PayPal once you reach the threshold."
        elif "cover" in user_input.lower():
            response += "For cover songs, you must obtain a mechanical license unless you use our distribution partner's cover song clearing service."
        
        with st.chat_message("assistant"):
            st.write(response)
        add_message("assistant", response)

# 3. DISTRIBUTION FLOW MODE (The Main Machine)
else:
    # We use a placeholder for inputs so they appear at the bottom or flow naturally
    input_placeholder = st.empty()

    # --- STEP: TITLE ---
    if st.session_state.step == "title":
        user_input = st.chat_input("Enter release title...")
        if user_input:
            add_message("user", user_input)
            # AI Extraction Logic
            extracted_title = simulate_ai_extraction(user_input, "title")
            st.session_state.user_data["Release Title"] = extracted_title
            
            response = f"Got it. I've set the title to **'{extracted_title}'**. \n\nNow, select the **Version Type**."
            add_message("assistant", response)
            st.session_state.step = "version"
            st.rerun()

    # --- STEP: VERSION (Dropdown Logic) ---
    elif st.session_state.step == "version":
        # Using a form container to make it look like a UI step
        with st.container():
            version_options = [
                "Original", "Alternate Take", "Instrumental", "Radio Edit", "Extended", 
                "Remastered", "Sped Up", "Slowed Down", "Lo-Fi", "Acapella", 
                "Acoustic", "Deluxe", "Demo", "Freestyle", "Karaoke", 
                "Live", "Remix", "Slowed and Reverb", "Other"
            ]
            
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_version = st.selectbox("Select Version Type", version_options, key="ver_select")
            
            # Conditional Logic Variables
            year_input = None
            remix_confirm = False
            other_input = None

            # Conditional UI
            if selected_version == "Remastered":
                year_input = st.number_input("Year of Original Version", min_value=1900, max_value=2024)
            
            if selected_version == "Remix":
                st.warning("⚠️ Remix Policy Check")
                remix_confirm = st.checkbox("I confirm I have the rights/permission for this remix.")

            if selected_version == "Other":
                other_input = st.text_input("Please specify the version type:")

            if st.button("Confirm Version"):
                # Validation
                valid = True
                final_version_string = selected_version

                if selected_version == "Remix" and not remix_confirm:
                    st.error("Please confirm you understand the remix policy to proceed.")
                    valid = False
                
                if selected_version == "Other":
                    if not other_input:
                        st.error("Please specify the version.")
                        valid = False
                    # Forbidden words check for "Other"
                    forbidden = ['Original', 'Official', 'Explicit', 'New']
                    if any(x.lower() in other_input.lower() for x in forbidden):
                        st.error(f"🚫 FORBIDDEN: You cannot use words like {forbidden} in custom versions.")
                        valid = False
                    final_version_string = other_input

                if valid:
                    # Save Data
                    if selected_version == "Remastered":
                        st.session_state.user_data["Version"] = f"Remastered ({year_input})"
                    else:
                        st.session_state.user_data["Version"] = final_version_string
                    
                    add_message("assistant", f"Version set to: **{st.session_state.user_data['Version']}**.")
                    add_message("assistant", "Who is the **Primary Artist**?")
                    st.session_state.step = "artist"
                    st.rerun()

    # --- STEP: ARTIST ---
    elif st.session_state.step == "artist":
        user_input = st.chat_input("Enter artist name...")
        if user_input:
            add_message("user", user_input)
            st.session_state.user_data["Primary Artist"] = user_input
            add_message("assistant", f"Artist is **{user_input}**. What is the **Genre**?")
            st.session_state.step = "genre"
            st.rerun()

    # --- STEP: GENRE ---
    elif st.session_state.step == "genre":
        user_input = st.chat_input("Enter genre...")
        if user_input:
            add_message("user", user_input)
            st.session_state.user_data["Genre"] = user_input
            add_message("assistant", "Great. Please upload your **Cover Art**.")
            st.session_state.step = "cover_art"
            st.rerun()

    # --- STEP: COVER ART UPLOAD ---
    elif st.session_state.step == "cover_art":
        uploaded_file = st.file_uploader("Upload 3000x3000px JPG/PNG", type=['jpg', 'png'])
        if uploaded_file:
            # Simulate "checking" the image
            with st.spinner("Analyzing image for text compliance..."):
                time.sleep(1.5)
            
            st.image(uploaded_file, width=300, caption="Uploaded Art")
            st.session_state.cover_image = uploaded_file
            
            st.warning("⚠️ Detect Text: 'Listen Now on Spotify' found on image.")
            st.info("Stores reject cover art with marketing text. We can fix this with AI.")
            
            if st.button("✨ Auto-Fix with AI"):
                st.session_state.step = "cover_fix"
                st.rerun()

    # --- STEP: COVER FIX PREVIEW ---
    elif st.session_state.step == "cover_fix":
        st.markdown("### 🖼️ Cover Art Clean-Up")
        col1, col2 = st.columns(2)
        with col1:
            st.image(st.session_state.cover_image, caption="Original (Rejected)")
        with col2:
            # In real life, this would be the processed image buffer
            # We use the same one for demo but imagine it's clean
            st.image(st.session_state.cover_image, caption="✨ AI Fixed (Clean)", output_format="JPEG")
            st.success("Removed: 'Listen Now on Spotify' text.")
        
        if st.button("✅ Confirm & Use This Art"):
            st.session_state.user_data["Cover Art Status"] = "Cleaned by AI"
            add_message("assistant", "Cover art confirmed clean! Now, please upload your **Audio File** (.wav/.mp3).")
            st.session_state.step = "audio"
            st.rerun()

    # --- STEP: AUDIO & ACR SIMULATION ---
    elif st.session_state.step == "audio":
        audio_file = st.file_uploader("Upload Audio", type=['wav', 'mp3'])
        if audio_file:
            st.audio(audio_file)
            
            if st.button("Submit Audio"):
                with st.status("🎚️ Processing Audio...", expanded=True) as status:
                    st.write("Checking format...")
                    time.sleep(1)
                    st.write("Scanning for explicit content...")
                    time.sleep(1)
                    st.write("🤖 Running ACR (Copyright Check)...")
                    time.sleep(1.5)
                    
                    # Randomly simulate a flag for demonstration
                    is_flagged = True 
                    
                    if is_flagged:
                        status.update(label="⚠️ Potential Match Found", state="warning")
                    else:
                        status.update(label="✅ Audio Clean", state="complete")
                
                if is_flagged:
                    st.warning("Our AI heard a sample that sounds like 'Shape of You'.")
                    st.write("Is this a cover song?")
                    col1, col2 = st.columns(2)
                    if col1.button("Yes, it's a cover"):
                        st.session_state.user_data["Type"] = "Cover"
                        st.session_state.step = "contributors"
                        st.rerun()
                    if col2.button("No, it's original"):
                        st.session_state.user_data["Type"] = "Original"
                        st.session_state.step = "contributors"
                        st.rerun()

    # --- STEP: CONTRIBUTORS ---
    elif st.session_state.step == "contributors":
        st.write("Do you have other contributors?")
        has_contributors = st.radio("Contributors?", ["No", "Yes"])
        
        if has_contributors == "Yes":
            c_name = st.text_input("Contributor Name")
            c_role = st.multiselect("Role", ["Featured Artist", "Producer", "Lyricist", "Composer", "Engineer"])
            if st.button("Add Contributor"):
                if "Contributors" not in st.session_state.user_data:
                    st.session_state.user_data["Contributors"] = []
                st.session_state.user_data["Contributors"].append(f"{c_name} ({', '.join(c_role)})")
                st.success(f"Added {c_name}")
        
        if st.button("Finish & Review"):
            st.session_state.step = "summary"
            st.rerun()

    # --- STEP: SUMMARY ---
    elif st.session_state.step == "summary":
        st.title("🚀 Release Ready!")
        st.json(st.session_state.user_data)
        st.balloons()
        
        if st.button("Start New Release"):
            st.session_state.clear()
            st.rerun()
