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

# --- 2. CONFIGURATION & STYLING ---
st.set_page_config(page_title="BandLab Distribution AI", page_icon="🔥", layout="centered")

st.markdown("""
<style>
    /* GLOBAL THEME */
    .stApp { background-color: #ffffff; color: #222; font-family: -apple-system, sans-serif; }
    
    /* CHAT BUBBLES */
    .stChatMessage {
        background-color: #f9f9f9;
        border: 1px solid #eee;
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 10px;
    }
    
    /* AI BADGES */
    .ai-badge {
        font-size: 0.7em; padding: 2px 8px; border-radius: 10px;
        background: #e0e0e0; color: #555; font-weight: bold;
        display: inline-block; margin-left: 8px; font-family: monospace;
    }
    
    /* BANDLAB BUTTONS */
    .stButton > button {
        border-radius: 20px; font-weight: 600;
        border: 1px solid #ddd; background-color: white; color: #333;
        transition: 0.2s; width: 100%; margin-bottom: 5px;
    }
    .stButton > button:hover {
        border-color: #F50000; color: #F50000; background-color: #fff5f5;
    }
    
    /* Hide Streamlit Footer */
    footer {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- 3. AI ENGINE (ROBUST) ---

def ask_ai(prompt):
    """
    Returns (Response_Text, Source_Label)
    """
    sys_prompt = "You are a concise BandLab Distribution expert. Explain in 1-2 short sentences."
    
    # 1. Groq (Llama 3)
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

    # 4. Fallback Database
    kb = {
        "Title": "The Release Title must match your cover art exactly. Avoid adding 'feat.' or producer tags here.",
        "Version": "Versions allow you to distinguish 'Radio Edits', 'Remixes', or 'Live' recordings from the original.",
        "Genre": "Genre metadata helps DSPs pitch your music to the correct editorial playlists.",
        "Date": "Scheduling a release 2+ weeks in advance gives you time to pitch to Spotify editors.",
        "UPC": "Universal Product Code (UPC) is the barcode used to track sales of your product.",
        "Label": "The Record Label field determines what appears in the 'Source' line on Spotify.",
        "Composers": "Publishing royalties are paid to songwriters. Legal First/Last names are required.",
        "Performers": "Listing performers ensures credit accuracy in the DSP databases.",
        "Language": "Language metadata routes your music to the correct regional teams at Apple/Spotify.",
        "Explicit": "You must flag 'Explicit' if lyrics contain violence, drugs, or profanity.",
        "Cover Art": "Art must be 3000x3000px JPG/PNG. No blurred images, URLs, or social handles.",
        "Audio": "We recommend High-Res WAV files (16-bit/44.1kHz or higher) for best quality."
    }
    # Keyword Search
    for k, v in kb.items():
        if k in prompt: return v, "Knowledge Base"
        
    return "This field is required for distribution metadata.", "Logic"

def get_edu_context(step_name):
    """Generates the education tip text"""
    # Map step keys to questions
    prompts = {
        "S1_TITLE": "Explain 'Release Title' rules for Spotify.",
        "S1_VERSION": "What is a 'Version' in music metadata?",
        "S1_GENRE": "Why is genre selection important for distribution?",
        "S1_DATE": "Why should I schedule a release date in advance?",
        "S1_UPC": "What is a UPC code?",
        "S1_LABEL": "What is a Record Label name field used for?",
        "S2_COMP_START": "Why do I need legal names for Composers?",
        "S2_PERF_START": "Who counts as a Performer on a track?",
        "S2_LANG": "Why does Spotify need the lyrics language?",
        "S2_EXPL": "What are the rules for Explicit content?",
        "S3_COVER": "What are the requirements for Cover Art?",
        "S3_AUDIO": "What audio format is best for distribution?"
    }
    
    if step_name in prompts:
        return ask_ai(prompts[step_name])
    return None, None

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

def add_msg(role, content, badge=None):
    st.session_state.messages.append({"role": role, "content": content, "badge": badge})

def process_input(user_text=None, next_step_id=None, bot_text=None, data_key=None, data_val=None, list_append=None):
    """
    Main Logic Processor
    """
    # 1. Record User Input
    if user_text:
        add_msg("user", user_text)
    
    # 2. Update Data
    if data_key:
        st.session_state.data[data_key] = data_val
    if list_append:
        st.session_state.data[list_append].append(data_val)
        
    # 3. Advance Step
    if next_step_id:
        st.session_state.step = next_step_id
        
        # 4. Add Bot Question
        add_msg("assistant", bot_text)
        
        # 5. TRIGGER EDUCATION (If Mode On)
        if st.session_state.edu_mode:
            tip, source = get_edu_context(next_step_id)
            if tip:
                add_msg("assistant", f"ℹ️ **Learn Mode:** {tip}", badge=source)
    
    st.rerun()

# --- 5. MAIN APP ---

init()

# SIDEBAR
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/BandLab_Technologies_logo.svg/2560px-BandLab_Technologies_logo.svg.png", width=140)
    st.markdown("### 🤖 Agent Settings")
    
    # Toggle Education
    mode = st.toggle("Enable AI Tips", value=st.session_state.edu_mode)
    if mode != st.session_state.edu_mode:
        st.session_state.edu_mode = mode
        st.rerun()
        
    st.divider()
    if st.button("Reset Chat"):
        st.session_state.clear()
        st.rerun()

# CHAT RENDERING
st.title("BandLab Distribution AI")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("badge"):
            st.markdown(f"<span class='ai-badge'>⚡ {msg['badge']}</span>", unsafe_allow_html=True)

# INPUT HANDLING
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
    # Date picker fallback
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
        # Add artist and skip manual input
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
            # Add performer logic manually here to handle dictionary
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
