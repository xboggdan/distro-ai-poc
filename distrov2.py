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
    /* GLOBAL RESET & DARK MODE FIX */
    .stApp { background-color: #FFFFFF; color: #333333; font-family: -apple-system, sans-serif; }
    
    /* INPUT FIELDS (Force Dark Text) */
    .stTextInput > div > div > input { color: #333333 !important; }
    
    /* CHAT BUBBLES */
    .user-msg {
        background-color: #F50000; color: white; padding: 12px 18px; 
        border-radius: 18px 18px 0 18px; margin: 8px 0 8px auto; 
        max-width: 70%; width: fit-content; box-shadow: 0 2px 6px rgba(245,0,0,0.2);
    }
    .bot-msg {
        background-color: #F3F4F6; color: #1F2937; padding: 12px 18px; 
        border-radius: 18px 18px 18px 0; margin: 8px auto 8px 0; 
        max-width: 70%; width: fit-content; border: 1px solid #E5E7EB;
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
    .badge-req { color: #DC2626; font-weight: 700; font-size: 0.8em; } /* Red for Required */
    .badge-done { color: #059669; font-weight: 700; font-size: 0.8em; } /* Green for Done */
    .badge-opt { color: #9CA3AF; font-size: 0.8em; font-style: italic; } /* Grey for Optional */

    /* BUTTONS */
    .stButton > button {
        border-radius: 8px; border: 1px solid #ddd; background: #f9f9f9; color: #333;
        font-size: 0.9em; padding: 8px; width: 100%;
    }
    .stButton > button:hover { border-color: #F50000; color: #F50000; background: #fff5f5; }

</style>
""", unsafe_allow_html=True)

# --- 3. THE "TRUE LLM" BRAIN ---

def call_llm_agent(messages, current_data):
    """
    Intelligent Agent that extracts intent and updates the JSON state.
    """
    
    # 1. Define Fields Schema (Strictly separated)
    req_fields = ["title", "artist", "genre", "date", "composers", "performers", "producers", "explicit"]
    opt_fields = ["label", "upc", "isrc", "version"]
    
    # 2. System Prompt
    system_prompt = f"""
    You are DistroBot, an expert A&R Agent.
    
    CURRENT METADATA STATE:
    {json.dumps(current_data, indent=2)}
    
    GOAL: Fill all REQUIRED fields ({req_fields}) first. Group OPTIONAL fields ({opt_fields}) at the end.
    
    LOGIC RULES:
    1. **Solo Artist Shortcut:** If the user implies they did everything, update 'composers', 'performers', AND 'producers' with the Main Artist's name.
    2. **Editing:** If the user says "Change X to Y" or "Remove X", update the state accordingly. Send null or empty list to clear fields.
    3. **Education:** If the user asks a question ("What is X?"), explain it simply in 1 sentence, THEN immediately ask if they want to proceed with that field (e.g., "Do you want me to generate one?").
    4. **Persona:** Efficient, helpful, smart.
    
    OUTPUT JSON FORMAT:
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
    
    # Simple keyword extraction mock
    if "title" in text: updates["title"] = "Extracted Title"
    if "hip hop" in text: updates["genre"] = "Hip Hop"
    if "isrc" in text and "?" in text:
        return {"response": "An ISRC is a unique ID for your track. I can generate one for free. Do you want that?", "updates": {}}
    if "generate" in text:
        updates["isrc"] = "US-S1Z-24-00001"
        return {"response": "Done! Generated ISRC: US-S1Z-24-00001. Ready for cover art?", "updates": updates}
    if "remove" in text:
        updates["performers"] = [data["artist"]] # Reset to just artist
        return {"response": "Removed the featured artist.", "updates": updates}
        
    return {"response": "I am offline (No Keys). Please enter keys or use Demo Mode.", "updates": updates}

# --- 4. STATE MANAGEMENT ---

def init_state():
    if "messages" not in st.session_state:
        st.session_state.update({
            "messages": [{"role": "assistant", "content": "🔥 **Welcome to BandLab Distribution.**\n\nI'm your AI Agent. Tell me about your release (Title, Artist, Genre) and I'll handle the metadata."}],
            "data": {
                # REQUIRED
                "title": None,
                "artist": "xboggdan", # Pre-filled from login
                "genre": None,
                "date": None,
                "composers": [],
                "performers": [],
                "producers": [],
                "explicit": None, 
                # OPTIONAL
                "version": None,
                "label": None,
                "upc": None,
                "isrc": None,
                # ASSETS
                "cover_status": False,
                "audio_status": False
            },
            "processing": False
        })

def process_input(user_input):
    if not user_input: return
    
    # 1. Add User Message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 2. Run AI Agent
    with st.spinner("🤖 analyzing intent..."):
        result = call_llm_agent(st.session_state.messages, st.session_state.data)
        
        # 3. Apply Updates
        updates = result.get("updates", {})
        for k, v in updates.items():
            if k in st.session_state.data:
                # Handle lists specifically (if AI sends string instead of list, wrap it)
                if isinstance(st.session_state.data[k], list) and not isinstance(v, list):
                    st.session_state.data[k] = [v] if v else []
                else:
                    st.session_state.data[k] = v
        
        # 4. Add Bot Response
        st.session_state.messages.append({"role": "assistant", "content": result.get("response")})
        
    st.rerun()

# --- 5. UI COMPONENTS ---

def render_status_row(label, value, required=True):
    status_class = "badge-req" if required and not value else "badge-done" if value else "badge-opt"
    
    # Text Logic
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
            
    st.markdown(f"""
    <div class="field-row">
        <span class="field-name">{label}</span>
        <span class="{status_class}">{status_text}</span>
    </div>
    """, unsafe_allow_html=True)

def render_dashboard():
    d = st.session_state.data
    st.markdown("### 💿 Live Draft")
    
    # SECTION 1: CORE DETAILS
    st.markdown("<div class='status-header'>1. Core Details</div>", unsafe_allow_html=True)
    render_status_row("Release Title", d['title'])
    render_status_row("Main Artist", d['artist'])
    render_status_row("Genre", d['genre'])
    render_status_row("Release Date", d['date'])
    
    # SECTION 2: CREDITS
    st.markdown("<div class='status-header'>2. Credits</div>", unsafe_allow_html=True)
    render_status_row("Composers", d['composers'])
    render_status_row("Performers", d['performers'])
    render_status_row("Producers", d['producers'])
    
    # SECTION 3: CONTENT
    st.markdown("<div class='status-header'>3. Content & Assets</div>", unsafe_allow_html=True)
    render_status_row("Explicit / Lang", d['explicit'])
    render_status_row("Cover Art", d['cover_status'])
    render_status_row("Master Audio", d['audio_status'])
    
    # SECTION 4: OPTIONAL
    with st.expander("Optional Metadata (Click to View)"):
        render_status_row("Version", d['version'], required=False)
        render_status_row("Label", d['label'], required=False)
        render_status_row("UPC", d['upc'], required=False)
        render_status_row("ISRC", d['isrc'], required=False)

def render_chat():
    for msg in st.session_state.messages:
        cls = "user-msg" if msg['role'] == "user" else "bot-msg"
        st.markdown(f"<div class='{cls}'>{msg['content']}</div>", unsafe_allow_html=True)
    st.markdown("<div id='end'></div>", unsafe_allow_html=True)

# --- 6. DEMO SCENARIOS (HAPPY PATHS) ---

def trigger_demo(scenario):
    st.session_state.messages = [] 
    init_state() 
    
    if scenario == "1":
        # ONE-SHOT
        process_input("I want to release a Hip Hop single called 'Empire' by xboggdan dropping ASAP.")
    
    elif scenario == "2":
        # SOLO ARTIST SHORTCUT
        st.session_state.data.update({"title": "Empire", "genre": "Hip Hop", "date": "ASAP"})
        st.session_state.messages.append({"role": "assistant", "content": "Metadata set. Now for credits: Are you the sole writer, performer, and producer?"})
        process_input("Yes, I did everything myself.")
        
    elif scenario == "4":
        # COMPLEX EDITING (Indecisive User)
        # 1. Set initial state
        st.session_state.data.update({"title": "Midnight Blue", "genre": "Pop"})
        st.session_state.messages.append({"role": "assistant", "content": "Draft created: 'Midnight Blue' (Pop)."})
        
        # 2. User changes mind on title
        process_input("Actually, change the title to 'Neon Lights'.")
        
        # 3. User adds a feature
        st.session_state.messages.append({"role": "assistant", "content": "Title updated to 'Neon Lights'. Any featured artists?"})
        process_input("Yeah, add 'Drake' as a featured vocalist.")
        
        # 4. User removes feature (Simulated via next input for flow speed, or distinct steps)
        # In a real demo, you'd click this button multiple times or split it. 
        # Here we simulate the final state of indecision leading to a result.
        time.sleep(1)
        st.session_state.messages.append({"role": "assistant", "content": "Added Drake. Anything else?"})
        process_input("Actually, remove Drake. I want to keep it solo.")

    elif scenario == "5":
        # EDUCATIONAL INTERRUPT
        st.session_state.data.update({"title": "Empire", "genre": "Hip Hop"})
        st.session_state.messages.append({"role": "assistant", "content": "Got it. Do you have an ISRC code for this track?"})
        
        # User asks question
        process_input("Wait, what is an ISRC? I'm new to this.")
        # Bot should explain AND ask to generate in response (Handled by LLM Prompt)

# --- 7. MAIN APP FLOW ---

init_state()

# SIDEBAR
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/BandLab_Technologies_logo.svg/2560px-BandLab_Technologies_logo.svg.png", width=140)
    
    render_dashboard()
    
    st.divider()
    st.markdown("### ⚡ Complex Demo Flows")
    if st.button("Scenario 1: One-Shot Entry"): trigger_demo("1")
    if st.button("Scenario 2: 'Solo Artist' Shortcut"): trigger_demo("2")
    if st.button("Scenario 4: The 'Indecisive Artist' (Edits)"): trigger_demo("4")
    if st.button("Scenario 5: 'Curious Beginner' (Edu Flow)"): trigger_demo("5")
    
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
            
        audio = c2.file_uploader("Audio", type=["wav", "mp3"], key="u_a")
        if audio and not st.session_state.data['audio_status']:
            st.session_state.data['audio_status'] = True
            st.toast("Audio Analysis Complete", icon="✅")
            st.rerun()

# CHAT INPUT
st.chat_input("Type your reply...", key="u_in", on_submit=lambda: process_input(st.session_state.u_in))
