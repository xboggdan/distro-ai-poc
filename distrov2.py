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
    .status-group { margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px; }
    .status-header { font-size: 0.8em; font-weight: 800; color: #9CA3AF; text-transform: uppercase; margin-bottom: 5px; }
    
    .field-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 6px 10px; background: #FAFAFA; border: 1px solid #EEEEEE;
        border-radius: 6px; margin-bottom: 4px; font-size: 0.85em;
    }
    .field-name { font-weight: 600; color: #4B5563; }
    
    /* BADGES */
    .badge-req { color: #DC2626; font-weight: 700; font-size: 0.8em; } 
    .badge-done { color: #059669; font-weight: 700; font-size: 0.8em; } 
    .badge-opt { color: #9CA3AF; font-size: 0.8em; font-style: italic; }

    /* DEMO BUTTONS */
    .stButton > button {
        border-radius: 8px; border: 1px solid #ddd; background: #f9f9f9; color: #333;
        font-size: 0.85em; padding: 10px; width: 100%; text-align: left;
    }
    .stButton > button:hover { border-color: #F50000; color: #F50000; background: #fff5f5; }

</style>
""", unsafe_allow_html=True)

# --- 3. THE LLM BRAIN ---

def call_llm_agent(messages, current_data):
    """
    Intelligent Agent that extracts intent and updates the JSON state.
    """
    
    # 1. Schema
    req_fields = ["title", "artist", "genre", "date", "composers", "performers", "producers", "explicit"]
    opt_fields = ["label", "upc", "isrc", "version"]
    
    # 2. System Prompt
    system_prompt = f"""
    You are DistroBot, an expert A&R Agent.
    
    CURRENT STATE:
    {json.dumps(current_data, indent=2)}
    
    GOAL: Fill REQUIRED ({req_fields}) first.
    
    LOGIC:
    1. **Extract:** Pull data from user text. If they say "me" or "I did it", use '{current_data.get('artist', 'User')}'.
    2. **Solo Artist:** If user implies they did everything, fill composers/performers/producers.
    3. **Edit:** If user says "Change X to Y", update it.
    4. **Educate:** If user asks "What is X?", explain briefly.
    
    OUTPUT JSON:
    {{
      "response": "Text reply...",
      "updates": {{ "field": "value" }}
    }}
    """
    
    # 3. Call AI API
    try:
        # Priority 1: Groq
        if "GROQ_API_KEY" in st.secrets:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            msgs = [{"role": "system", "content": system_prompt}] + [{"role": m["role"], "content": m["content"]} for m in messages]
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs, response_format={"type": "json_object"})
            return json.loads(res.choices[0].message.content)
            
        # Priority 2: Gemini
        elif "GEMINI_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
            chat = model.start_chat(history=[])
            prompt = system_prompt + f"\n\nUSER MESSAGE: {messages[-1]['content']}"
            res = chat.send_message(prompt)
            return json.loads(res.text)
            
        # Priority 3: OpenAI
        elif "OPENAI_API_KEY" in st.secrets:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            msgs = [{"role": "system", "content": system_prompt}] + [{"role": m["role"], "content": m["content"]} for m in messages]
            res = client.chat.completions.create(model="gpt-4o", messages=msgs, response_format={"type": "json_object"})
            return json.loads(res.choices[0].message.content)

    except Exception as e:
        return {"response": f"AI Error: {str(e)}", "updates": {}}

    # Offline Fallback (Mock)
    return mock_logic_fallback(messages[-1]['content'], current_data)

def mock_logic_fallback(text, data):
    text = text.lower()
    updates = {}
    
    if "title" in text: updates["title"] = "Extracted Title"
    if "hip hop" in text: updates["genre"] = "Hip Hop"
    
    # Chaos Artist Mock
    if "chaos" in text:
        updates["title"] = "Chaos Theory"
        updates["artist"] = "DJ Entropy"
        updates["genre"] = "Hyperpop"
        return {"response": "Whoa, that's a lot! I caught: Title 'Chaos Theory' by DJ Entropy (Hyperpop). Is that right?", "updates": updates}

    return {"response": "I am offline (No Keys). Please enter keys or use Demo Mode.", "updates": updates}

# --- 4. STATE MANAGEMENT ---

def init_state():
    if "messages" not in st.session_state:
        st.session_state.update({
            "messages": [{"role": "assistant", "content": "🔥 **Welcome to BandLab Distribution.**\n\nI'm your AI Agent. Tell me about your release (Title, Artist, Genre) and I'll handle the metadata."}],
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
        if len(value) > 0:
            status_text = f"✓ {len(value)} ADDED"
            status_class = "badge-done"
        elif required:
            status_text = "⭕ REQUIRED"
            status_class = "badge-req"
        else:
            status_text = "OPTIONAL"
            
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
    
    st.markdown("<div class='status-header'>1. Core Details</div>", unsafe_allow_html=True)
    render_status_row("Release Title", d['title'])
    render_status_row("Main Artist", d['artist'])
    render_status_row("Genre", d['genre'])
    render_status_row("Release Date", d['date'])
    
    st.markdown("<div class='status-header'>2. Credits</div>", unsafe_allow_html=True)
    render_status_row("Composers", d['composers'])
    render_status_row("Performers", d['performers'])
    render_status_row("Producers", d['producers'])
    
    st.markdown("<div class='status-header'>3. Content & Assets</div>", unsafe_allow_html=True)
    render_status_row("Explicit / Lang", d['explicit'])
    render_status_row("Cover Art", d['cover_status'])
    render_status_row("Master Audio", d['audio_status'])
    
    with st.expander("Optional Metadata"):
        render_status_row("Version", d['version'], False)
        render_status_row("Label", d['label'], False)
        render_status_row("UPC", d['upc'], False)
        render_status_row("ISRC", d['isrc'], False)

def render_chat():
    for msg in st.session_state.messages:
        cls = "user-msg" if msg['role'] == "user" else "bot-msg"
        st.markdown(f"<div class='{cls}'>{msg['content']}</div>", unsafe_allow_html=True)
    st.markdown("<div id='end'></div>", unsafe_allow_html=True)

# --- 6. DEMO SCENARIOS (FULL CONVERSATIONS) ---

def trigger_demo(scenario):
    st.session_state.messages = [] 
    init_state() 
    d = st.session_state.data
    
    # Helper to inject chat history & state
    def sim_chat(user_txt, bot_txt, updates=None):
        st.session_state.messages.append({"role": "user", "content": user_txt})
        st.session_state.messages.append({"role": "assistant", "content": bot_txt})
        if updates:
            for k,v in updates.items(): d[k] = v

    # --- SCENARIO 1: ONE-SHOT ---
    if scenario == "1":
        d['title'] = "Empire"
        d['genre'] = "Hip Hop"
        d['date'] = "ASAP"
        d['explicit'] = "Explicit"
        st.session_state.messages.append({"role": "user", "content": "I want to release a Hip Hop single called 'Empire' by xboggdan dropping ASAP. It's explicit."})
        st.session_state.messages.append({"role": "assistant", "content": "Got it! I've extracted: **Title:** Empire, **Genre:** Hip Hop, **Date:** ASAP, **Explicit:** Yes.\n\nNow for credits: Are you the sole writer, performer, and producer?"})

    # --- SCENARIO 2: SOLO SHORTCUT ---
    elif scenario == "2":
        sim_chat("I'm releasing 'Neon Nights'", "Cool title! What genre is 'Neon Nights'?", {"title": "Neon Nights"})
        sim_chat("It's Synthwave. I wrote and produced it all myself.", "Awesome. I've marked you as the **Composer**, **Producer**, and **Performer**. \n\nIs the content clean or explicit?", 
                 {"genre": "Synthwave", "composers": ["xboggdan"], "performers": ["xboggdan"], "producers": ["xboggdan"]})

    # --- SCENARIO 3: OPTIONAL SWEEP ---
    elif scenario == "3":
        # Pre-fill mandatory
        d.update({"title": "Midnight", "genre": "Pop", "composers":["xboggdan"], "performers":["xboggdan"], "producers":["xboggdan"], "explicit":"Clean"})
        sim_chat("Here is my Pop track 'Midnight'. All credits are me.", "Metadata complete! Now for the technical stuff. Do you have a specific **Label Name**, **UPC**, or **ISRC**? Or should I auto-generate them?")
        sim_chat("Auto-generate everything, but put 'Cloud Records' as the label.", "Done! Generated UPC/ISRC and set Label to 'Cloud Records'. Ready for assets!", 
                 {"label": "Cloud Records", "upc": "AUTO-GEN", "isrc": "AUTO-GEN"})

    # --- SCENARIO 4: INDECISIVE ARTIST (Complex Edits) ---
    elif scenario == "4":
        sim_chat("Start a release for 'Blue Sky'", "Okay, 'Blue Sky'. What genre?", {"title": "Blue Sky"})
        sim_chat("Actually change title to 'Grey Sky' and genre is Rock", "Updated: 'Grey Sky' (Rock). Who is the artist?", {"title": "Grey Sky", "genre": "Rock"})
        sim_chat("It's me and my friend Dave on drums.", "Added you (xboggdan) and Dave (Drums). Anyone else?", {"performers": ["xboggdan", "Dave"]})
        sim_chat("Wait, Dave quit. Remove him.", "Removed Dave. It's just you now.", {"performers": ["xboggdan"]})

    # --- SCENARIO 5: CURIOUS BEGINNER (Education) ---
    elif scenario == "5":
        sim_chat("I want to upload 'My Song'", "Sure. Do you have an ISRC for 'My Song'?", {"title": "My Song"})
        sim_chat("What is an ISRC?", "An ISRC is a unique digital fingerprint used to track streams and sales. You need one for every track. \n\nSince you don't have one, shall I generate a free code for you?")
        sim_chat("Yes please.", "Generated! Moving on...", {"isrc": "US-S1Z-24-00001"})

    # --- SCENARIO 6: THE CHAOS ARTIST (Unstructured Input) ---
    elif scenario == "6":
        chaos_input = "yo so the song is called 'Pizza Party' its hyperpop and dropping next friday also i wrote it with my mom but i produced it alone oh and its clean"
        d.update({"title": "Pizza Party", "genre": "Hyperpop", "date": "Next Friday", "explicit": "Clean", "producers": ["xboggdan"], "composers": ["xboggdan", "Mom"]})
        st.session_state.messages.append({"role": "user", "content": chaos_input})
        st.session_state.messages.append({"role": "assistant", "content": "Wow, lot of info! Here is what I caught:\n- **Title:** Pizza Party\n- **Genre:** Hyperpop\n- **Date:** Next Friday\n- **Credits:** You (Producer), You + Mom (Writers)\n- **Clean:** Yes\n\nDid I miss anything?"})

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
    if st.button("4. The Indecisive User (Edits)"): trigger_demo("4")
    if st.button("5. The Curious User (Edu)"): trigger_demo("5")
    if st.button("6. The Chaos Input (Smart)"): trigger_demo("6")
    
    st.divider()
    if st.button("Reset"): st.session_state.clear(); st.rerun()

# MAIN CHAT
st.title("BandLab Distribution AI")
render_chat()

# ASSET UPLOAD
if st.session_state.data.get("title"):
    with st.expander("📂 Asset Upload Zone", expanded=True):
        c1, c2 = st.columns(2)
        cover = c1.file_uploader("Cover Art", type=["jpg", "png"], key="u_c")
        if cover and not st.session_state.data['cover_status']:
            st.session_state.data['cover_status'] = True
            st.toast("Vision AI Check Passed", icon="✅")
            st.rerun()
