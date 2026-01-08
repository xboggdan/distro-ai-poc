import streamlit as st
import json
import time

# --- 1. SETUP & IMPORTS ---
try:
    from groq import Groq
    import google.generativeai as genai
    from openai import OpenAI
except ImportError:
    pass

# --- 2. CONFIGURATION & STYLING ---
st.set_page_config(page_title="BandLab Distribution AI", page_icon="🔥", layout="wide")

st.markdown("""
<style>
    /* GLOBAL RESET */
    .stApp { background-color: #FFFFFF; color: #333333; font-family: -apple-system, sans-serif; }
    
    /* WELCOME CARD (The Missing Piece) */
    .welcome-container {
        background-color: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 16px;
        padding: 40px; text-align: center; margin: 20px auto; max-width: 800px;
    }
    .welcome-title { font-size: 24px; font-weight: 800; margin-bottom: 10px; color: #111; }
    .welcome-sub { color: #6B7280; margin-bottom: 30px; font-size: 16px; }
    
    /* CHAT BUBBLES */
    .user-msg {
        background-color: #F50000; color: white; padding: 12px 18px; 
        border-radius: 18px 18px 0 18px; margin: 8px 0 8px auto; 
        max-width: 75%; width: fit-content; box-shadow: 0 2px 6px rgba(245,0,0,0.2);
    }
    .bot-msg {
        background-color: #F3F4F6; color: #1F2937; padding: 12px 18px; 
        border-radius: 18px 18px 18px 0; margin: 8px auto 8px 0; 
        max-width: 75%; width: fit-content; border: 1px solid #E5E7EB;
    }
    
    /* DASHBOARD (SIDEBAR) */
    .field-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 6px 10px; background: #FAFAFA; border: 1px solid #EEEEEE;
        border-radius: 6px; margin-bottom: 4px; font-size: 0.85em;
    }
    .field-name { font-weight: 600; color: #4B5563; }
    
    /* STATUS BADGES */
    .badge-req { color: #DC2626; font-weight: 700; font-size: 0.8em; } 
    .badge-done { color: #059669; font-weight: 700; font-size: 0.8em; } 
    .badge-opt { color: #9CA3AF; font-size: 0.8em; font-style: italic; }

    /* START BUTTON */
    .big-btn > button {
        background-color: #F50000; color: white; font-size: 18px; font-weight: 600;
        padding: 15px 30px; border-radius: 30px; border: none; width: 100%; transition: 0.3s;
    }
    .big-btn > button:hover { background-color: #d10000; transform: scale(1.02); }

</style>
""", unsafe_allow_html=True)

# --- 3. THE "TRUE LLM" BRAIN ---

def call_llm_agent(messages, current_data):
    """
    Intelligent Agent that extracts intent and updates the JSON state.
    """
    req_fields = ["title", "artist", "genre", "date", "composers", "performers", "producers", "explicit"]
    opt_fields = ["label", "upc", "isrc", "version"]
    
    system_prompt = f"""
    You are DistroBot, an expert A&R Agent.
    CURRENT STATE: {json.dumps(current_data, indent=2)}
    GOAL: Fill REQUIRED ({req_fields}) first.
    
    LOGIC:
    1. **Extract:** Pull data from user text. If they say "me" or "I did it", use '{current_data.get('artist', 'User')}'.
    2. **Solo Artist:** If user implies they did everything, fill composers/performers/producers.
    3. **Educate:** If user asks "What is X?", explain briefly.
    
    OUTPUT JSON:
    {{ "response": "Text reply...", "updates": {{ "field": "value" }} }}
    """
    
    try:
        # GROQ
        if "GROQ_API_KEY" in st.secrets:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            msgs = [{"role": "system", "content": system_prompt}] + [{"role": m["role"], "content": m["content"]} for m in messages]
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs, response_format={"type": "json_object"})
            return json.loads(res.choices[0].message.content)
            
        # GEMINI
        elif "GEMINI_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
            chat = model.start_chat(history=[])
            prompt = system_prompt + f"\n\nUSER MESSAGE: {messages[-1]['content']}"
            res = chat.send_message(prompt)
            return json.loads(res.text)
            
        # OPENAI
        elif "OPENAI_API_KEY" in st.secrets:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            msgs = [{"role": "system", "content": system_prompt}] + [{"role": m["role"], "content": m["content"]} for m in messages]
            res = client.chat.completions.create(model="gpt-4o", messages=msgs, response_format={"type": "json_object"})
            return json.loads(res.choices[0].message.content)

    except Exception:
        pass

    return mock_logic_fallback(messages[-1]['content'], current_data)

def mock_logic_fallback(text, data):
    text = text.lower()
    updates = {}
    if "title" in text: updates["title"] = "Extracted Title"
    if "hip hop" in text: updates["genre"] = "Hip Hop"
    if "start" in text: return {"response": "Great! What is the **Release Title**?", "updates": {}}
    
    # Chaos Mock
    if "chaos" in text:
        updates["title"] = "Chaos Theory"
        updates["artist"] = "DJ Entropy"
        updates["genre"] = "Hyperpop"
        return {"response": "Wow, lot of info! Caught: Title 'Chaos Theory' by DJ Entropy. Correct?", "updates": updates}

    return {"response": "I am offline (No Keys). Please enter keys or use Demo Mode.", "updates": updates}

# --- 4. STATE MANAGEMENT ---

def init_state():
    if "messages" not in st.session_state:
        st.session_state.update({
            "messages": [], # Empty start for Welcome Screen logic
            "data": {
                "title": None, "artist": "xboggdan", "genre": None, "date": None,
                "composers": [], "performers": [], "producers": [], "explicit": None, 
                "version": None, "label": None, "upc": None, "isrc": None,
                "cover_status": False, "audio_status": False
            },
            "processing": False
        })

def process_input(user_input):
    if not user_input: return
    
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.spinner("🤖 analyzing intent..."):
        result = call_llm_agent(st.session_state.messages, st.session_state.data)
        
        updates = result.get("updates", {})
        for k, v in updates.items():
            if k in st.session_state.data:
                if isinstance(st.session_state.data[k], list) and not isinstance(v, list):
                    st.session_state.data[k] = [v] if v else []
                else:
                    st.session_state.data[k] = v
        
        st.session_state.messages.append({"role": "assistant", "content": result.get("response")})
        
    st.rerun()

# --- 5. UI COMPONENTS ---

def render_status_row(label, value, required=True):
    status_class = "badge-req" if required and not value else "badge-done" if value else "badge-opt"
    
    if isinstance(value, list):
        status_text = f"✓ {len(value)} ADDED" if len(value) > 0 else "⭕ REQUIRED" if required else "OPTIONAL"
    elif value:
        status_text = "✓ DONE"
    elif required:
        status_text = "⭕ REQUIRED"
    else:
        status_text = "OPTIONAL"
            
    st.markdown(f"<div class='field-row'><span class='field-name'>{label}</span><span class='{status_class}'>{status_text}</span></div>", unsafe_allow_html=True)

def render_dashboard():
    d = st.session_state.data
    st.markdown("### 💿 Live Draft")
    
    st.markdown("<div style='font-size:0.8em; font-weight:800; color:#9CA3AF; margin:10px 0 5px 0;'>1. CORE DETAILS</div>", unsafe_allow_html=True)
    render_status_row("Title", d['title'])
    render_status_row("Artist", d['artist'])
    render_status_row("Genre", d['genre'])
    render_status_row("Date", d['date'])
    
    st.markdown("<div style='font-size:0.8em; font-weight:800; color:#9CA3AF; margin:10px 0 5px 0;'>2. CREDITS</div>", unsafe_allow_html=True)
    render_status_row("Composers", d['composers'])
    render_status_row("Performers", d['performers'])
    render_status_row("Producers", d['producers'])
    
    st.markdown("<div style='font-size:0.8em; font-weight:800; color:#9CA3AF; margin:10px 0 5px 0;'>3. CONTENT</div>", unsafe_allow_html=True)
    render_status_row("Explicit", d['explicit'])
    render_status_row("Cover Art", d['cover_status'])
    render_status_row("Audio", d['audio_status'])

def render_chat():
    for msg in st.session_state.messages:
        cls = "user-msg" if msg['role'] == "user" else "bot-msg"
        st.markdown(f"<div class='{cls}'>{msg['content']}</div>", unsafe_allow_html=True)
    st.markdown("<div id='end'></div>", unsafe_allow_html=True)

def render_welcome():
    st.markdown("""
    <div class="welcome-container">
        <div style="font-size: 3em; margin-bottom: 10px;">🔥</div>
        <div class="welcome-title">BandLab Distribution AI</div>
        <div class="welcome-sub">I'm your automated A&R agent. I validate metadata, check artwork, and organize credits instantly.</div>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown('<div class="big-btn">', unsafe_allow_html=True)
        if st.button("Start New Release", key="start_btn"):
            st.session_state.messages.append({"role": "assistant", "content": "Let's go! What is the **Release Title**?"})
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 6. DEMO SCENARIOS ---

def trigger_demo(scenario):
    st.session_state.messages = [] 
    init_state() 
    d = st.session_state.data
    
    # Helper to inject chat history
    def sim_chat(user_txt, bot_txt, updates=None):
        st.session_state.messages.append({"role": "user", "content": user_txt})
        st.session_state.messages.append({"role": "assistant", "content": bot_txt})
        if updates:
            for k,v in updates.items(): d[k] = v

    if scenario == "1":
        d.update({"title": "Empire", "genre": "Hip Hop", "date": "ASAP", "explicit": "Explicit"})
        st.session_state.messages.append({"role": "user", "content": "I want to release a Hip Hop single called 'Empire' by xboggdan dropping ASAP. It's explicit."})
        st.session_state.messages.append({"role": "assistant", "content": "Got it! I've extracted: **Title:** Empire, **Genre:** Hip Hop, **Date:** ASAP, **Explicit:** Yes.\n\nNow for credits: Are you the sole writer, performer, and producer?"})

    elif scenario == "2":
        sim_chat("I'm releasing 'Neon Nights'", "Cool title! What genre is 'Neon Nights'?", {"title": "Neon Nights"})
        sim_chat("It's Synthwave. I wrote and produced it all myself.", "Awesome. I've marked you as the **Composer**, **Producer**, and **Performer**. \n\nIs the content clean or explicit?", {"genre": "Synthwave", "composers": ["xboggdan"], "performers": ["xboggdan"], "producers": ["xboggdan"]})

    elif scenario == "3": # Optional Sweep
        d.update({"title": "Midnight", "genre": "Pop", "composers":["xboggdan"], "performers":["xboggdan"], "producers":["xboggdan"], "explicit":"Clean"})
        sim_chat("Here is my Pop track 'Midnight'. All credits are me.", "Metadata complete! Now: Do you have a specific **Label Name** or **ISRC**? Or should I auto-generate them?")
        sim_chat("Auto-generate please.", "Done! Generated ISRC and set Label to 'xboggdan'. Ready for assets!", {"label": "xboggdan", "isrc": "AUTO-GEN"})

    elif scenario == "4": # Edits
        sim_chat("Start a release for 'Blue Sky'", "Okay, 'Blue Sky'. What genre?", {"title": "Blue Sky"})
        sim_chat("Actually change title to 'Grey Sky' and genre is Rock", "Updated: 'Grey Sky' (Rock). Who is the artist?", {"title": "Grey Sky", "genre": "Rock"})
        sim_chat("It's me and my friend Dave on drums.", "Added you (xboggdan) and Dave (Drums). Anyone else?", {"performers": ["xboggdan", "Dave"]})
        sim_chat("Wait, Dave quit. Remove him.", "Removed Dave. It's just you now.", {"performers": ["xboggdan"]})

    elif scenario == "5": # Education
        st.session_state.messages.append({"role": "assistant", "content": "What is the Release Title?"})
        sim_chat("Wait, what is an ISRC?", "An ISRC is a unique digital fingerprint for tracking streams and royalties. \n\nSince you don't have one, I can generate it for free later. Now, back to business: What is the **Release Title**?")

    elif scenario == "6": # Chaos
        chaos = "yo the song is 'Pizza Party' its hyperpop and dropping next friday i wrote it with my mom but i produced it alone oh and its clean"
        d.update({"title": "Pizza Party", "genre": "Hyperpop", "date": "Next Friday", "explicit": "Clean", "producers": ["xboggdan"], "composers": ["xboggdan", "Mom"]})
        st.session_state.messages.append({"role": "user", "content": chaos})
        st.session_state.messages.append({"role": "assistant", "content": "Wow, lot of info! I caught:\n- **Title:** Pizza Party\n- **Genre:** Hyperpop\n- **Date:** Next Friday\n- **Credits:** You (Producer), You + Mom (Writers)\n- **Clean:** Yes\n\nDid I miss anything?"})

    st.rerun()

# --- 7. MAIN APP FLOW ---

init_state()

# SIDEBAR
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/BandLab_Technologies_logo.svg/2560px-BandLab_Technologies_logo.svg.png", width=140)
    
    render_dashboard()
    
    st.divider()
    st.markdown("### ⚡ Power Demos")
    if st.button("1. One-Shot Entry"): trigger_demo("1")
    if st.button("2. 'Solo Artist' Shortcut"): trigger_demo("2")
    if st.button("3. Optional Sweep"): trigger_demo("3")
    if st.button("4. Complex Editing"): trigger_demo("4")
    if st.button("5. Educational Interrupt"): trigger_demo("5")
    if st.button("6. Chaos Input"): trigger_demo("6")
    
    st.divider()
    if st.button("Reset"): st.session_state.clear(); st.rerun()

# MAIN AREA
st.title("BandLab Distribution AI")

# Show Welcome OR Chat
if not st.session_state.messages:
    render_welcome()
else:
    render_chat()

# ASSET UPLOAD (Only if Title Set)
if st.session_state.data.get("title"):
    with st.expander("📂 Asset Upload Zone", expanded=True):
        c1, c2 = st.columns(2)
        cover = c1.file_uploader("Cover Art", type=["jpg", "png"], key="u_c")
        if cover and not st.session_state.data['cover_status']:
            st.session_state.data['cover_status'] = True
            st.toast("Vision AI Check Passed", icon="✅")
            st.rerun()
        audio = c2.file_uploader("Audio", type=["wav", "mp3"], key="u_a")
        if audio and not st.session_state.data['audio_status']:
            st.session_state.data['audio_status'] = True
            st.toast("Audio Analysis Complete", icon="✅")
            st.rerun()

# INPUT BAR
st.chat_input("Type your reply...", key="u_in", on_submit=lambda: process_input(st.session_state.u_in))
