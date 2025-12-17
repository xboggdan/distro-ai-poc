import streamlit as st
import time
import uuid

# --- 1. SETUP & IMPORTS ---
try:
    from groq import Groq
    import google.generativeai as genai
    from openai import OpenAI
except ImportError:
    pass

# --- 2. CONFIGURATION & VISUAL STYLING ---
st.set_page_config(page_title="BandLab Distribution AI", page_icon="🔥", layout="centered")

st.markdown("""
<style>
    /* --- 1. RESET & THEME FORCING (Fixes Dark Mode Issues) --- */
    .stApp {
        background-color: #FFFFFF;
        color: #333333 !important; /* Forces dark text even if user is in Dark Mode */
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Hide Streamlit Boilerplate */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* --- 2. CHAT BUBBLES --- */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 15px;
        margin-bottom: 30px;
    }
    
    .bubble {
        padding: 12px 18px;
        border-radius: 18px;
        font-size: 15px;
        line-height: 1.5;
        max-width: 85%;
        position: relative;
        animation: fadeIn 0.3s ease;
    }
    
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    
    /* User Bubble (Right, Red) */
    .user-bubble {
        background-color: #F50000;
        color: white !important;
        align-self: flex-end;
        border-bottom-right-radius: 4px;
        margin-left: auto;
        box-shadow: 0 2px 5px rgba(245,0,0,0.2);
    }
    
    /* Bot Bubble (Left, Grey) */
    .bot-bubble {
        background-color: #F3F4F6;
        color: #1F2937 !important;
        align-self: flex-start;
        border-bottom-left-radius: 4px;
        margin-right: auto;
        border: 1px solid #E5E7EB;
    }
    
    /* --- 3. EDUCATIONAL INSIGHT CARD --- */
    .edu-card {
        background-color: #FFFBEB;
        border: 1px solid #FCD34D;
        color: #92400E !important;
        padding: 12px 16px;
        border-radius: 12px;
        font-size: 14px;
        margin-top: -5px;
        margin-bottom: 10px;
        align-self: flex-start;
        max-width: 85%;
        display: flex;
        gap: 10px;
        align-items: flex-start;
    }
    .edu-icon { font-size: 16px; margin-top: 2px; }
    .ai-badge {
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        background: rgba(0,0,0,0.05);
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 8px;
        font-weight: bold;
    }

    /* --- 4. INPUT AREA STYLING --- */
    /* Make buttons look clickable and high-end */
    .stButton > button {
        border: 1px solid #E5E7EB;
        background-color: #FFFFFF;
        color: #374151 !important;
        border-radius: 12px;
        padding: 12px 20px;
        font-weight: 600;
        width: 100%;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        border-color: #F50000;
        color: #F50000 !important;
        background-color: #FFF5F5;
        transform: translateY(-1px);
    }
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 1px solid #E5E7EB;
        padding: 10px 15px;
        color: #333 !important;
    }

</style>
""", unsafe_allow_html=True)

# --- 3. AI ENGINE (ROBUST & SILENT FALLBACK) ---

def get_fallback_answer(topic):
    """Hardcoded answers guaranteed to exist if AI fails"""
    kb = {
        "S1_TITLE": "Your Release Title must match the cover art exactly. Do not include 'feat.' or producer tags in the main title.",
        "S1_VERSION": "Versions distinguish this release from the original, such as 'Radio Edit', 'Remix', or 'Instrumental'.",
        "S1_GENRE": "Selecting the correct primary Genre ensures your music is pitched to the right editorial playlists.",
        "S1_DATE": "We recommend scheduling your release at least 2 weeks in advance to allow time for playlist pitching.",
        "S1_UPC": "A UPC (Universal Product Code) is a barcode used to track sales of your product across all stores.",
        "S1_LABEL": "The Record Label name appears in the 'Source' line on Spotify. Independent artists often use their own name.",
        "S2_COMP_START": "Streaming services pay publishing royalties to songwriters. Legal names are required to collect this money.",
        "S2_PERF_START": "Listing performers (instrumentalists/vocalists) ensures accurate credits in the global music database.",
        "S2_LANG": "Specifying the lyrics language helps DSPs route your music to the correct regional moderation teams.",
        "S2_EXPL": "You must mark a track as Explicit if it contains profanity, violence, or references to drug use.",
        "S3_COVER": "Cover Art must be 3000x3000px JPG or PNG. No blurred images, URLs, pricing, or social handles allowed.",
        "S3_AUDIO": "For best quality, upload High-Res WAV files (16-bit/44.1kHz or higher). MP3s are accepted but less ideal."
    }
    # Default fallback
    return kb.get(topic, "This metadata field is required for correct distribution."), "Knowledge Base"

def ask_ai(step_id):
    """
    Returns (Response_Text, Source_Label)
    """
    # Map step ID to a human-readable prompt
    prompts = {
        "S1_TITLE": "Explain 'Release Title' rules for Spotify.",
        "S1_VERSION": "What is a 'Version' in music metadata?",
        "S1_GENRE": "Why is genre selection important?",
        "S1_DATE": "Why schedule a release date in advance?",
        "S1_UPC": "What is a UPC code?",
        "S1_LABEL": "What is a Record Label name used for?",
        "S2_COMP_START": "Why do I need legal names for Composers?",
        "S2_PERF_START": "Who counts as a Performer?",
        "S2_LANG": "Why does Spotify need lyrics language?",
        "S2_EXPL": "Rules for Explicit content?",
        "S3_COVER": "Requirements for Cover Art?",
        "S3_AUDIO": "Best audio format for distribution?"
    }
    
    prompt = prompts.get(step_id)
    if not prompt:
        return None, None

    sys_prompt = "You are a concise BandLab Distribution expert. Explain in 1 sentence."

    # 1. Groq
    if "GROQ_API_KEY" in st.secrets:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            res = client.chat.completions.create(
                messages=[{"role":"system","content":sys_prompt},{"role":"user","content":prompt}],
                model="llama-3.3-70b-versatile"
            )
            return res.choices[0].message.content, "Llama 3"
        except: pass

    # 2. Gemini
    if "GEMINI_API_KEY" in st.secrets:
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(prompt)
            return res.text, "Gemini"
        except: pass

    # 3. GPT
    if "OPENAI_API_KEY" in st.secrets:
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role":"system","content":sys_prompt},{"role":"user","content":prompt}]
            )
            return res.choices[0].message.content, "GPT-4"
        except: pass

    # 4. Fallback
    return get_fallback_answer(step_id)

# --- 4. STATE MANAGEMENT ---

def init():
    if "messages" not in st.session_state:
        st.session_state.update({
            "messages": [
                {"role": "assistant", "content": "🔥 **Welcome to BandLab Distribution.**\n\nI am your AI A&R Agent. I'll guide you through the process.\n\nFirst, what is the **Release Title** of your song?"}
            ],
            "step": "S1_TITLE",
            "edu_mode": False,
            "data": {
                "title": "", "version": "", "artist": "xboggdan", "genre": "", 
                "date": "ASAP", "label": "", "upc": "",
                "composers": [], "performers": [], "producers": [],
                "lang": "English", "explicit": "Clean", "isrc": "",
                "cover": None, "audio": None
            },
            "temp_name": ""
        })

def add_msg(role, content, is_edu=False, badge=None):
    st.session_state.messages.append({
        "role": role, 
        "content": content, 
        "is_edu": is_edu,
        "badge": badge
    })

def process_input(user_text=None, next_step_id=None, bot_text=None, data_key=None, data_val=None, list_append=None):
    # 1. Record User
    if user_text:
        add_msg("user", user_text)
    
    # 2. Save Data
    if data_key:
        st.session_state.data[data_key] = data_val
    if list_append:
        st.session_state.data[list_append].append(data_val)
        
    # 3. Advance Step
    if next_step_id:
        st.session_state.step = next_step_id
        add_msg("assistant", bot_text)
        
        # 4. Trigger Edu Mode
        if st.session_state.edu_mode:
            explanation, source = ask_ai(next_step_id)
            if explanation:
                add_msg("assistant", explanation, is_edu=True, badge=source)
    
    st.rerun()

# --- 5. UI COMPONENTS (HTML RENDERING) ---

def render_chat():
    chat_html = '<div class="chat-container">'
    
    for msg in st.session_state.messages:
        # User Message
        if msg['role'] == "user":
            chat_html += f'<div class="bubble user-bubble">{msg["content"]}</div>'
        
        # Educational Insight Card
        elif msg.get('is_edu'):
            chat_html += f"""
            <div class="edu-card">
                <div class="edu-icon">💡</div>
                <div>
                    {msg['content']}
                    <span class="ai-badge">⚡ {msg['badge']}</span>
                </div>
            </div>
            """
        
        # Bot Message
        else:
            chat_html += f'<div class="bubble bot-bubble">{msg["content"]}</div>'
            
    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)

# --- 6. MAIN APP FLOW ---

init()

# SIDEBAR
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/BandLab_Technologies_logo.svg/2560px-BandLab_Technologies_logo.svg.png", width=140)
    
    # Edu Toggle
    st.markdown("### 🎓 Learning Mode")
    mode = st.toggle("Enable AI Tips", value=st.session_state.edu_mode)
    if mode != st.session_state.edu_mode:
        st.session_state.edu_mode = mode
        st.rerun()
        
    st.divider()
    if st.button("Reset Chat"):
        st.session_state.clear()
        st.rerun()

# TITLE
st.title("BandLab Distribution AI")

# RENDER CHAT HISTORY
render_chat()

# INPUT LOGIC
step = st.session_state.step
d = st.session_state.data

# --- STEP 1: TITLE ---
if step == "S1_TITLE":
    if val := st.chat_input("Enter Song Title..."):
        process_input(val, "S1_VERSION", "Does this release have a specific **Version** (e.g. Radio Edit)?", "title", val)

# --- STEP 2: VERSION ---
elif step == "S1_VERSION":
    c1, c2 = st.columns(2)
    if c1.button("No, Original Mix"):
        process_input("Original Mix", "S1_GENRE", "Select the primary **Genre**.", "version", "")
    if val := st.chat_input("Enter Version (e.g. Remix)..."):
        process_input(val, "S1_GENRE", "Select the primary **Genre**.", "version", val)

# --- STEP 3: GENRE ---
elif step == "S1_GENRE":
    genres = ["Hip Hop", "Pop", "Rock", "R&B", "Electronic", "Alternative", "Country", "Latin"]
    cols = st.columns(4)
    for i, g in enumerate(genres):
        if cols[i%4].button(g, use_container_width=True):
            process_input(g, "S1_DATE", "When should we release this?", "genre", g)

# --- STEP 4: DATE ---
elif step == "S1_DATE":
    if st.button("ASAP (As Soon As Possible)"):
        process_input("ASAP", "S1_UPC", "Do you have a **UPC Barcode**?", "date", "ASAP")
    dval = st.date_input("Or Pick Date", label_visibility="collapsed")
    if st.button("Confirm Date"):
        process_input(str(dval), "S1_UPC", "Do you have a **UPC Barcode**?", "date", str(dval))

# --- STEP 5: UPC ---
elif step == "S1_UPC":
    if st.button("Generate Free UPC"):
        process_input("Generate Free", "S1_LABEL", "What is the **Record Label** name?", "upc", "AUTO")
    if val := st.chat_input("Enter 12-digit UPC..."):
        process_input(val, "S1_LABEL", "What is the **Record Label** name?", "upc", val)

# --- STEP 6: LABEL ---
elif step == "S1_LABEL":
    if st.button(f"Use '{d['artist']}'"):
        process_input(d['artist'], "S2_COMP_START", f"Credits: Is **{d['artist']}** the Composer (Songwriter)?", "label", d['artist'])
    if val := st.chat_input("Enter Label Name..."):
        process_input(val, "S2_COMP_START", f"Credits: Is **{d['artist']}** the Composer (Songwriter)?", "label", val)

# --- STEP 7: COMPOSER START ---
elif step == "S2_COMP_START":
    c1, c2 = st.columns(2)
    if c1.button("Yes, It's Me"):
        st.session_state.data['composers'].append(d['artist'])
        process_input("Yes", "S2_COMP_LOOP", "Composer added. Do you need to add anyone else?")
    if c2.button("No / Someone Else"):
        process_input("Someone Else", "S2_COMP_MANUAL", "Enter the Composer's **Legal Name**.")

# --- STEP 8: COMPOSER MANUAL ---
elif step == "S2_COMP_MANUAL":
    if val := st.chat_input("Legal First & Last Name..."):
        process_input(val, "S2_COMP_LOOP", "Composer added. Do you need to add anyone else?", list_append="composers", data_val=val)

# --- STEP 9: COMPOSER LOOP ---
elif step == "S2_COMP_LOOP":
    c1, c2 = st.columns(2)
    if c1.button("No, I'm Done"):
        process_input("Done", "S2_PERF_START", f"Did **{d['artist']}** perform on this track?")
    if c2.button("Add Another"):
        process_input("Add Another", "S2_COMP_MANUAL", "Enter the next Composer's **Legal Name**.")

# --- STEP 10: PERFORMER START ---
elif step == "S2_PERF_START":
    c1, c2 = st.columns(2)
    if c1.button("Yes"):
        st.session_state.temp_name = d['artist']
        process_input("Yes", "S2_PERF_ROLE", f"What instrument did **{d['artist']}** play?")
    if c2.button("No / Someone Else"):
        process_input("Someone Else", "S2_PERF_MANUAL", "Enter the Performer's Name.")

# --- STEP 11: PERFORMER ROLE ---
elif step == "S2_PERF_ROLE":
    roles = ["Vocals", "Guitar", "Bass", "Drums", "Keys", "Other"]
    cols = st.columns(3)
    for i, r in enumerate(roles):
        if cols[i%3].button(r, use_container_width=True):
            st.session_state.data['performers'].append({"name": st.session_state.temp_name, "role": r})
            process_input(r, "S2_PERF_LOOP", "Performer added. Anyone else?")

# --- STEP 12: PERFORMER MANUAL ---
elif step == "S2_PERF_MANUAL":
    if val := st.chat_input("Performer Name..."):
        st.session_state.temp_name = val
        process_input(val, "S2_PERF_ROLE", f"What instrument did **{val}** play?")

# --- STEP 13: PERFORMER LOOP ---
elif step == "S2_PERF_LOOP":
    c1, c2 = st.columns(2)
    if c1.button("Done"):
        process_input("Done", "S2_LANG", "What is the **Lyrics Language**?")
    if c2.button("Add Another"):
        process_input("Add Another", "S2_PERF_MANUAL", "Enter the Performer's Name.")

# --- STEP 14: LANGUAGE ---
elif step == "S2_LANG":
    c1, c2 = st.columns(2)
    if c1.button("English"):
        process_input("English", "S2_EXPL", "Is the content **Explicit**?", "lang", "English")
    if c2.button("Instrumental (No Lyrics)"):
        process_input("Instrumental", "S3_COVER", "Upload your **Cover Art**.", "lang", "Instrumental")

# --- STEP 15: EXPLICIT ---
elif step == "S2_EXPL":
    c1, c2 = st.columns(2)
    if c1.button("Clean / Safe"):
        process_input("Clean", "S3_COVER", "Upload your **Cover Art**.", "explicit", "Clean")
    if c2.button("Explicit (Parental Advisory)"):
        process_input("Explicit", "S3_COVER", "Upload your **Cover Art**.", "explicit", "Explicit")

# --- STEP 16: COVER ART ---
elif step == "S3_COVER":
    f = st.file_uploader("JPG/PNG 3000px", type=["jpg", "png"], label_visibility="collapsed")
    if f:
        st.session_state.data['cover'] = f
        process_input("Image Uploaded", "S3_AUDIO", "Upload your **Master Audio** (WAV/MP3).")

# --- STEP 17: AUDIO ---
elif step == "S3_AUDIO":
    f = st.file_uploader("WAV/MP3", type=["wav", "mp3"], label_visibility="collapsed")
    if f:
        st.session_state.data['audio'] = f
        process_input("Audio Uploaded", "REVIEW", "🎉 All set! Review your release below.")

# --- REVIEW ---
elif step == "REVIEW":
    st.write("---")
    st.subheader("📝 Release Summary")
    st.json(d)
    if st.button("🚀 SUBMIT TO STORES", type="primary"):
        st.balloons()
        st.success("Submitted successfully!")
