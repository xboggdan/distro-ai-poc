import streamlit as st
import time
import openai 

# --- CONFIGURATION & SECRETS ---
st.set_page_config(page_title="BandLab Distribution Assistant", page_icon="🚀", layout="wide")

# Try to load API key from secrets
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    has_api_key = True
except:
    has_api_key = False

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    h1, h2, h3 { color: #d13239; font-family: 'Helvetica Neue', sans-serif; }
    .stChatMessage { background-color: white; border-radius: 10px; padding: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .success-box { padding: 20px; background-color: #d4edda; color: #155724; border-radius: 10px; border: 1px solid #c3e6cb; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "step" not in st.session_state: st.session_state.step = 1
if "release_data" not in st.session_state:
    st.session_state.release_data = {"title": "New Single", "file": None, "genre": "", "cover": None}
if "main_chat" not in st.session_state:
    st.session_state.main_chat = [{"role": "assistant", "content": "Let's get your **Single** ready. \n\n**Step 1:** Please upload your Audio File."}]
if "kb_chat" not in st.session_state:
    st.session_state.kb_chat = [] # Separate history for Knowledge Base

# --- SIDEBAR: ACTIVE KNOWLEDGE BASE ---
with st.sidebar:
    st.header("🧠 Knowledge Base")
    
    if not has_api_key:
        st.error("⚠️ OpenAI Key missing in Secrets!")
    else:
        # Display KB Chat History
        for msg in st.session_state.kb_chat:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        
        # KB Input
        kb_question = st.text_input("Ask a question about distribution:", key="kb_input")
        if st.button("Ask Guide"):
            if kb_question:
                # 1. User Message
                st.session_state.kb_chat.append({"role": "user", "content": kb_question})
                
                # 2. AI Response
                with st.spinner("Thinking..."):
                    try:
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a music distribution expert for BandLab. Keep answers short and helpful."},
                                {"role": "user", "content": kb_question}
                            ]
                        )
                        answer = response.choices[0].message.content
                    except Exception as e:
                        answer = f"Error: {str(e)}"

                # 3. Save Response
                st.session_state.kb_chat.append({"role": "assistant", "content": answer})
                st.rerun()

# --- MAIN APP ---
st.title("🚀 BandLab Distribution Assistant")
st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 Release Wizard")

    # Render Main Chat
    for msg in st.session_state.main_chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # --- STEP 1: UPLOAD AUDIO ---
    if st.session_state.step == 1:
        uploaded_file = st.file_uploader("Select Audio File", type=['wav', 'mp3'], key="audio")
        if uploaded_file:
            st.session_state.release_data["file"] = uploaded_file.name
            st.session_state.main_chat.append({"role": "user", "content": f"Uploaded: **{uploaded_file.name}**"})
            st.session_state.main_chat.append({"role": "assistant", "content": "Audio valid! ✅ \n\n**Step 2:** What is the **Title**?"})
            st.session_state.step = 2
            st.rerun()

    # --- STEP 2: METADATA ---
    if st.session_state.step == 2:
        with st.form("meta_form"):
            title = st.text_input("Track Title", value=st.session_state.release_data["title"])
            genre = st.selectbox("Genre", ["Pop", "Hip-Hop", "Rock", "Electronic", "R&B"])
            if st.form_submit_button("Next ➡"):
                st.session_state.release_data.update({"title": title, "genre": genre})
                st.session_state.main_chat.append({"role": "user", "content": f"{title} ({genre})"})
                st.session_state.main_chat.append({"role": "assistant", "content": "Nice title. \n\n**Step 3:** Upload **Cover Art**."})
                st.session_state.step = 3
                st.rerun()

    # --- STEP 3: COVER ART ---
    if st.session_state.step == 3:
        cover_file = st.file_uploader("Upload Art (JPG/PNG)", type=['jpg', 'png'], key="cover")
        if cover_file:
            st.session_state.release_data["cover"] = cover_file
            st.session_state.main_chat.append({"role": "user", "content": "Cover art uploaded."})
            st.session_state.main_chat.append({"role": "assistant", "content": "Artwork looks great! \n\n**Step 4:** Review and Distribute."})
            st.session_state.step = 4
            st.rerun()

    # --- STEP 4: REVIEW & SUBMIT ---
    if st.session_state.step == 4:
        st.info("Please review your release details before submission.")
        
        # Summary Table
        st.table({
            "Track Title": [st.session_state.release_data["title"]],
            "Genre": [st.session_state.release_data["genre"]],
            "Audio File": [st.session_state.release_data["file"]],
            "Cover Art": ["Uploaded ✅"]
        })

        if st.button("🚀 Distribute to Spotify & Apple Music", type="primary"):
            with st.spinner("Uploading to servers..."):
                time.sleep(2) # Fake API call
                st.session_state.step = 5
                st.rerun()

    # --- STEP 5: SUCCESS ---
    if st.session_state.step == 5:
        st.markdown("""
        <div class="success-box">
            <h3>🎉 Release Submitted!</h3>
            <p>Your track <b>%s</b> has been sent to stores.</p>
            <p>You will receive an email when it goes live (usually 24-48 hours).</p>
        </div>
        """ % st.session_state.release_data["title"], unsafe_allow_html=True)
        
        if st.button("Start New Release"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

# --- RIGHT COLUMN: PREVIEW ---
with col2:
    st.subheader("👀 Preview")
    c = st.container(border=True)
    
    # Dynamic Cover Art
    if st.session_state.release_data["cover"]:
        c.image(st.session_state.release_data["cover"], use_container_width=True)
    else:
        c.image("https://placehold.co/400x400?text=Cover+Art", use_container_width=True)
        
    c.markdown(f"### {st.session_state.release_data['title']}")
    if st.session_state.release_data["genre"]:
        c.caption(st.session_state.release_data["genre"])
