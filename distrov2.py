import streamlit as st
import time

# 1. Page Configuration (Must be the first line)
st.set_page_config(
    page_title="BandLab Distribution Assistant",
    page_icon="🚀",
    layout="wide"  # Uses more screen real estate
)

# 2. Custom CSS for "BandLab" styling
st.markdown("""
    <style>
    /* Main container styling */
    .stApp {
        background-color: #f8f9fa; /* Light grey background for contrast */
    }
    /* Headers */
    h1, h2, h3 {
        color: #d13239; /* BandLab Red-ish color */
        font-family: 'Helvetica Neue', sans-serif;
    }
    /* Chat message styling */
    .stChatMessage {
        background-color: white;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Sidebar: The "Knowledge Base" lives here now (Cleaner UI)
with st.sidebar:
    st.header("🧠 Knowledge Base")
    st.info("I am listening to your conversation. If you ask a question, I will answer here.")
    
    with st.expander("How to use this guide", expanded=True):
        st.write("I'm your **Guide**. Ask me questions like *'What is a UPC?'* or *'Why do I need a legal name?'*.")

# 4. Main Content Area
st.title("🚀 BandLab Distribution Assistant")
st.markdown("---")

# Layout: We can keep it focused in the center or use columns if needed
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 Release Wizard")
    
    # Mocking the chat history for the demo
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Let's get your **Single** ready for Spotify. \n\n**Step 1:** Please upload your Audio File."}
        ]

    # Display chat messages nicely
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # File Uploader (Logic: Only show if waiting for file)
    uploaded_file = st.file_uploader("Select Audio File (WAV/MP3)", type=['wav', 'mp3'])
    
    if uploaded_file:
        with st.chat_message("user"):
            st.write(f"Uploaded: **{uploaded_file.name}**")
        
        # Simulate agent response
        with st.spinner("Analyzing audio..."):
            time.sleep(1) # Fake processing
            st.success("Audio validated successfully!")
            # Here you would trigger your backend logic

with col2:
    # Optional: Context sensitive help or preview
    st.subheader("👀 Preview")
    st.caption("As you fill in data, a preview of your release will appear here.")
    
    # Placeholder for a "Card" view of the release
    container = st.container(border=True)
    container.markdown("**New Single**")
    container.image("https://via.placeholder.com/150", caption="Cover Art Placeholder")