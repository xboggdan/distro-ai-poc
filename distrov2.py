import streamlit as st
import time

# 1. Page Configuration
st.set_page_config(page_title="BandLab Distribution Assistant", page_icon="🚀", layout="wide")

# 2. Custom CSS
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    h1, h2, h3 { color: #d13239; font-family: 'Helvetica Neue', sans-serif; }
    .stChatMessage { background-color: white; border-radius: 10px; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    /* Highlight the active step */
    .step-active { border-left: 5px solid #d13239; padding-left: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Sidebar
with st.sidebar:
    st.header("🧠 Knowledge Base")
    st.info("I am listening. Ask questions like 'What is an ISRC?' here.")
    with st.expander("Guide Options", expanded=True):
        st.write("Current Mode: **Single Release**")

# 4. Session State Management (The "Brain")
if "step" not in st.session_state:
    st.session_state.step = 1
if "release_data" not in st.session_state:
    st.session_state.release_data = {"title": "New Single", "file": None, "genre": ""}
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Let's get your **Single** ready. \n\n**Step 1:** Please upload your Audio File."}
    ]

# 5. Main Layout
st.title("🚀 BandLab Distribution Assistant")
st.markdown("---")

col1, col2 = st.columns([2, 1])

# --- LEFT COLUMN: THE WIZARD ---
with col1:
    st.subheader("📝 Release Wizard")

    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # --- STEP 1: UPLOAD ---
    if st.session_state.step == 1:
        uploaded_file = st.file_uploader("Select Audio File (WAV/MP3)", type=['wav', 'mp3'], key="audio_uploader")
        
        if uploaded_file:
            # Save file info
            st.session_state.release_data["file"] = uploaded_file.name
            
            # Show simulated processing
            with st.spinner("Analyzing audio fingerprint..."):
                time.sleep(1.5) 
            
            # Add completion message to chat
            st.session_state.messages.append({"role": "user", "content": f"Uploaded: **{uploaded_file.name}**"})
            st.session_state.messages.append({"role": "assistant", "content": "Audio looks good! ✅ \n\n**Step 2:** What is the **Title** of this track?"})
            
            # Advance to Step 2
            st.session_state.step = 2
            st.rerun()

    # --- STEP 2: METADATA ---
    if st.session_state.step == 2:
        with st.form("metadata_form"):
            st.write("Enter Track Details:")
            title_input = st.text_input("Track Title", value=st.session_state.release_data["title"])
            genre_input = st.selectbox("Genre", ["Pop", "Hip-Hop", "Rock", "Electronic", "R&B"])
            
            submitted = st.form_submit_button("Next Step ➡")
            
            if submitted:
                # Update Data
                st.session_state.release_data["title"] = title_input
                st.session_state.release_data["genre"] = genre_input
                
                # Add to chat
                st.session_state.messages.append({"role": "user", "content": f"Title: {title_input}, Genre: {genre_input}"})
                st.session_state.messages.append({"role": "assistant", "content": "Got it. \n\n**Step 3:** Now, please upload your **Cover Art** (3000x3000px)."})
                
                # Advance Step
                st.session_state.step = 3
                st.rerun()

    # --- STEP 3: ARTWORK (Demo End) ---
    if st.session_state.step == 3:
        st.file_uploader("Upload Cover Art (JPG/PNG)", type=['jpg', 'png'])
        st.info("Demo stops here for now. Backend connection required for next steps.")

# --- RIGHT COLUMN: REAL-TIME PREVIEW ---
with col2:
    st.subheader("👀 Preview")
    
    # Live Preview Card
    container = st.container(border=True)
    
    # 1. Cover Art (Placeholder or Real if uploaded)
    container.image("https://placehold.co/400x400?text=Cover+Art", use_container_width=True)
    
    # 2. Track Data
    container.markdown(f"### {st.session_state.release_data.get('title', 'New Single')}")
    
    genre_display = st.session_state.release_data.get('genre', '')
    if genre_display:
        container.caption(f"Genre: {genre_display}")
    
    # 3. File Status
    if st.session_state.release_data["file"]:
        container.success(f"🎵 File: {st.session_state.release_data['file']}")
    else:
        container.warning("🎵 No Audio File")
