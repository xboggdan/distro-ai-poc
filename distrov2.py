import streamlit as st
import time
import random

# --- CONFIGURATION ---
st.set_page_config(page_title="DistroBot V10", page_icon="💿", layout="wide")

# --- CSS FOR UI & TECH BADGES ---
st.markdown("""
<style>
    .stChatMessage {
        background-color: #f9f9f9;
        border-radius: 15px;
        padding: 10px;
        border: 1px solid #eee;
    }
    .tech-badge {
        font-size: 0.75em;
        color: #666;
        background-color: #e0e0e0;
        padding: 2px 6px;
        border-radius: 4px;
        margin-top: 5px;
        display: inline-block;
        font-family: monospace;
    }
    .source-logic { border-left: 3px solid #ffcc00; } /* Yellow for Backend Logic */
    .source-ai { border-left: 3px solid #00ccff; }    /* Blue for AI Agent */
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant", 
        "content": "Hello! I'm DistroBot V10. Let's get your music on Spotify. What is the **Release Title**?",
        "source": "Backend Logic",
        "model": "Hardcoded v1.0"
    }]
if "step" not in st.session_state:
    st.session_state.step = "title" 
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "mode" not in st.session_state:
    st.session_state.mode = "Distribution Flow"

# --- HELPER FUNCTIONS ---

def add_message(role, content, source="User", model="N/A"):
    st.session_state.messages.append({
        "role": role, 
        "content": content, 
        "source": source, 
        "model": model
    })

def simulate_ai_extraction(user_input):
    """
    Simulates extracting the core entity from a conversational sentence.
    """
    triggers = ["my title is", "release title is", "name is", "called"]
    cleaned = user_input
    
    # 1. AI Extraction Simulation
    lower_input = user_input.lower()
    for trigger in triggers:
        if trigger in lower_input:
            start_index = lower_input.find(trigger) + len(trigger)
            cleaned = user_input[start_index:].strip()
            cleaned = cleaned.strip('".')
            return cleaned, "NLP Entity Extraction", "GPT-4o-Mini (Simulated)"
            
    return user_input.strip(), "Direct Input", "Rule-Engine v2"

def get_educational_response(query):
    """
    Simulates a RAG (Retrieval Augmented Generation) response for the Educational Mode.
    """
    query = query.lower()
    
    # Knowledge Base Simulation
    kb = {
        "royalties": "You keep 100% of your royalties. We do not take a cut. Payouts are monthly via PayPal.",
        "membership": "No, you do not need a paid membership to distribute. Standard distribution is free.",
        "upc": "A UPC (Universal Product Code) is a unique barcode for your release. We generate one for you automatically for free.",
        "isrc": "ISRCs are unique codes for individual tracks. We assign these automatically if you don't have them.",
        "cover": "For cover songs, you must obtain a mechanical license. We can help you manage this via our partners.",
        "spotify": "Delivery to Spotify usually takes 24-48 hours after we approve your release.",
        "apple": "Apple Music ingestion can take up to 3-5 days depending on their review queue.",
        "life": "I am a robot, so I have no life, but I hope yours is filled with great music! 🎵"
    }
    
    # Simple Keyword Search
    for key, answer in kb.items():
        if key in query:
            return answer, "RAG (Retrieval)", "VectorDB + GPT-3.5"
    
    return "I can help with distribution, royalties, and metadata. Could you clarify your question?", "Fallback Logic", "Default Intent Classifier"

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎛 Control Center")
    mode = st.radio("Interaction Mode", ["Distribution Flow", "Educational / Help"], index=0 if st.session_state.mode == "Distribution Flow" else 1)
    
    if mode != st.session_state.mode:
        st.session_state.mode = mode
        st.rerun()

    st.divider()
    with st.expander("📝 Metadata Debugger", expanded=True):
        st.json(st.session_state.user_data)
        
    if st.button("Reset Session"):
        st.session_state.clear()
        st.rerun()

# --- MAIN RENDER LOOP ---

# 1. Display Chat History with Tech Details
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            # The "Tech Badge"
            st.markdown(f"""
            <div class='tech-badge' title='Technical details'>
               ⚙️ Source: {msg['source']} | 🧠 Model: {msg['model']}
            </div>
            """, unsafe_allow_html=True)

# 2. INPUT HANDLING

if st.session_state.mode == "Educational / Help":
    # EDUCATIONAL MODE LOGIC
    user_input = st.chat_input("Ask about Royalties, UPC, Membership...")
    if user_input:
        add_message("user", user_input)
        
        # Get smart response
        response_text, src, mdl = get_educational_response(user_input)
        
        add_message("assistant", response_text, source=src, model=mdl)
        st.rerun()

else:
    # DISTRIBUTION FLOW LOGIC
    
    # --- STEP: TITLE ---
    if st.session_state.step == "title":
        user_input = st.chat_input("Enter release title...")
        if user_input:
            add_message("user", user_input)
            
            extracted_title, source, model = simulate_ai_extraction(user_input)
            st.session_state.user_data["Release Title"] = extracted_title
            
            resp = f"Got it. Title set to: **'{extracted_title}'**."
            add_message("assistant", resp, source=source, model=model)
            
            # Transition
            time.sleep(0.5)
            st.session_state.step = "version"
            st.rerun()

    # --- STEP: VERSION (Dropdown) ---
    elif st.session_state.step == "version":
        # We render the dropdown inside a chat message to make it feel conversational
        with st.chat_message("assistant"):
            st.write("Select the **Version Type** below:")
            
            col1, col2 = st.columns([2,1])
            with col1:
                version_options = [
                    "Original", "Alternate Take", "Instrumental", "Radio Edit", "Extended", 
                    "Remastered", "Remix", "Other"
                ]
                selected_version = st.selectbox("Version Type", version_options, key="v_select")
            
            # Dynamic Fields
            year_input = None
            remix_confirm = False
            other_input = None
            
            if selected_version == "Remastered":
                year_input = st.number_input("Original Year", 1900, 2025)
            elif selected_version == "Remix":
                st.warning("⚠️ You must have permission for remixes.")
                remix_confirm = st.checkbox("I confirm I have rights.")
            elif selected_version == "Other":
                other_input = st.text_input("Specify Version Type")

            if st.button("Confirm Version"):
                # VALIDATION LOGIC
                valid = True
                final_ver = selected_version
                
                if selected_version == "Remix" and not remix_confirm:
                    st.error("❌ Permission confirmation required.")
                    valid = False
                elif selected_version == "Other":
                    forbidden = ['original', 'official', 'explicit']
                    if any(x in other_input.lower() for x in forbidden):
                        st.error(f"❌ Invalid term in custom version.")
                        valid = False
                    final_ver = other_input
                
                if valid:
                    if selected_version == "Remastered":
                        final_ver = f"Remastered ({year_input})"
                    
                    st.session_state.user_data["Version"] = final_ver
                    add_message("assistant", f"Version Type saved: **{final_ver}**", source="Validation Logic", model="Rule-Engine v1")
                    add_message("assistant", "Who is the **Primary Artist**?", source="Flow Controller", model="Hardcoded")
                    st.session_state.step = "artist"
                    st.rerun()

    # --- STEP: ARTIST ---
    elif st.session_state.step == "artist":
        user_input = st.chat_input("Enter Artist Name")
        if user_input:
            add_message("user", user_input)
            st.session_state.user_data["Artist"] = user_input
            add_message("assistant", f"Artist set to **{user_input}**. Upload **Cover Art**.", source="Backend Logic", model="N/A")
            st.session_state.step = "cover"
            st.rerun()

    # --- STEP: COVER ART ---
    elif st.session_state.step == "cover":
        uploaded_file = st.file_uploader("Upload Art (3000x3000px)", type=['jpg', 'png'])
        if uploaded_file:
            st.session_state.cover_image = uploaded_file
            st.image(uploaded_file, width=250, caption="Preview")
            
            if st.button("Analyze & Upload"):
                with st.spinner("🔍 Vision Model checking text..."):
                    time.sleep(1.5)
                
                # Simulate "Dirty" Art
                st.warning("⚠️ Text Detected: 'Listen on Spotify'")
                st.info("💡 Recommendation: Use AI to remove marketing text.")
                
                if st.button("✨ Auto-Fix (AI)"):
                    st.session_state.step = "cover_fix"
                    st.rerun()

    # --- STEP: COVER FIX ---
    elif st.session_state.step == "cover_fix":
        c1, c2 = st.columns(2)
        c1.image(st.session_state.cover_image, caption="Original")
        c2.image(st.session_state.cover_image, caption="✨ AI Fixed", output_format="JPEG") # Simulating change
        
        if st.button("Use Fixed Artwork"):
            add_message("assistant", "Art fixed and approved. Upload **Audio**.", source="Vision Pipeline", model="DALL-E 3 / Inpainting")
            st.session_state.step = "audio"
            st.rerun()

    # --- STEP: AUDIO ---
    elif st.session_state.step == "audio":
        audio = st.file_uploader("Upload WAV/MP3", type=['wav', 'mp3'])
        if audio:
            if st.button("Process Audio"):
                # FIX: Using 'error' state instead of 'warning'
                status = st.status("🎧 Processing Audio...", expanded=True)
                status.write("Checking format...")
                time.sleep(1)
                status.write("Running ACR (Copyright)...")
                time.sleep(1)
                
                # Flagged Simulation
                status.update(label="⚠️ Copyright Match Found", state="error")
                
                st.error("ACR Match: 'Shape of You' detected.")
                st.write("Is this a cover?")
                
                c1, c2 = st.columns(2)
                if c1.button("Yes, Cover"):
                    st.session_state.user_data["Type"] = "Cover"
                    add_message("assistant", "Marked as Cover. Any contributors?", source="ACR Cloud API", model="Audio Fingerprinting")
                    st.session_state.step = "contributors"
                    st.rerun()

    # --- STEP: CONTRIBUTORS ---
    elif st.session_state.step == "contributors":
        if st.button("No Contributors / Finish"):
            st.session_state.step = "finish"
            st.rerun()

    # --- STEP: FINISH ---
    elif st.session_state.step == "finish":
        st.success("Release Ready for Distribution!")
        st.json(st.session_state.user_data)
        if st.button("Start Over"):
            st.session_state.clear()
            st.rerun()
