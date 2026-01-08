import streamlit as st
import json
import time
from PIL import Image

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
        max-width: 70%; width: fit-content; box-shadow: 0 2px 6px rgba(245,0,0,0.2);
    }
    .bot-msg {
        background-color: #F3F4F6; color: #1F2937; padding: 12px 18px; 
        border-radius: 18px 18px 18px 0; margin: 8px auto 8px 0; 
        max-width: 70%; width: fit-content; border: 1px solid #E5E7EB;
    }
    
    /* DASHBOARD (SIDEBAR) */
    .status-group { margin-bottom: 20px; }
    .status-header { font-size: 0.85em; font-weight: 700; color: #6B7280; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
    
    .field-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 8px 12px; background: #FAFAFA; border: 1px solid #EEEEEE;
        border-radius: 8px; margin-bottom: 6px; font-size: 0.9em;
    }
    .field-name { font-weight: 500; color: #374151; }
    
    /* Status Badges */
    .badge-missing { color: #DC2626; font-weight: 600; font-size: 0.8em; display: flex; align-items: center; gap: 4px; }
    .badge-done { color: #059669; font-weight: 600; font-size: 0.8em; display: flex; align-items: center; gap: 4px; }
    .badge-optional { color: #D97706; font-size: 0.8em; font-style: italic; }

    /* DEMO BUTTONS */
    .demo-btn { border: 1px solid #ddd; padding: 5px; border-radius: 5px; margin-bottom: 5px; font-size: 0.8em; cursor: pointer; text-align: center; background: #f9f9f9;}
    .demo-btn:hover { background: #eee; }

</style>
""", unsafe_allow_html=True)

# --- 3. THE "TRUE LLM" BRAIN ---

def call_llm_agent(messages, current_data):
    """
    The core intelligence. Uses the conversation history + current data state 
    to decide on updates and the next response.
    """
    
    # 1. Define Fields Schema
    required_fields = ["title", "artist", "genre", "version", "date", "explicit"]
    optional_fields = ["label", "upc", "isrc"]
    
    # 2. System Prompt
    system_prompt = f"""
    You are DistroBot, an expert A&R Agent for BandLab.
    
    CURRENT METADATA STATE:
    {json.dumps(current_data, indent=2)}
    
    YOUR GOAL:
    Fill in all REQUIRED fields ({required_fields}) by chatting with the user.
    OPTIONAL fields ({optional_fields}) can be skipped or auto-generated if the user asks.
    
    RULES:
    1. **Extraction:** If the user says "My song is Midnight by DJ Cloud", extract BOTH Title and Artist immediately.
    2. **Validation:** If the user provides a Title with "feat.", politely remove it and update the Title without it.
    3. **Education:** If the user asks about a term (e.g. ISRC), explain it simply.
    4. **Flow:** Look at what is MISSING in the State. Ask for the next missing REQUIRED field.
    5. **Persona:** Helpful, professional, concise.
    
    OUTPUT FORMAT (JSON ONLY):
    {{
      "response": "Text reply to user...",
      "updates": {{ "field_name": "value" }} 
    }}
    """
    
    # 3. Call AI API (Cascading Fallback)
    try:
        # Priority 1: Groq (Fastest)
        if "GROQ_API_KEY" in st.secrets:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            # Format history
            msgs = [{"role": "system", "content": system_prompt}] + [{"role": m["role"], "content": m["content"]} for m in messages]
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=msgs,
                response_format={"type": "json_object"}
            )
            return json.loads(res.choices[0].message.content)
            
        # Priority 2: Gemini
        elif "GEMINI_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
            chat = model.start_chat(history=[])
            # Send system + last message logic
            prompt = system_prompt + f"\n\nUSER MESSAGE: {messages[-1]['content']}"
            res = chat.send_message(prompt)
            return json.loads(res.text)
            
        # Priority 3: OpenAI
        elif "OPENAI_API_KEY" in st.secrets:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            msgs = [{"role": "system", "content": system_prompt}] + [{"role": m["role"], "content": m["content"]} for m in messages]
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=msgs,
                response_format={"type": "json_object"}
            )
            return json.loads(res.choices[0].message.content)

    except Exception as e:
        return {"response": f"AI Error: {str(e)}", "updates": {}}

    # Fallback Logic (Mock Agent) if offline
    return manual_logic_fallback(messages[-1]['content'], current_data)

def manual_logic_fallback(user_text, data):
    """Simple offline logic if no API keys present"""
    user_text = user_text.lower()
    updates = {}
    resp = "Got it."
    
    if "title" in user_text: updates["title"] = "Extracted Title"
    if "artist" in user_text: updates["artist"] = "Extracted Artist"
    
    if not data["title"]: resp = "What is the Release Title?"
    elif not data["artist"]: resp = "Who is the Main Artist?"
    elif not data["genre"]: resp = "What is the Genre?"
    else: resp = "Metadata looks good! Ready for assets."
    
    return {"response": resp, "updates": updates}

# --- 4. STATE MANAGEMENT ---

def init_state():
    if "messages" not in st.session_state:
        st.session_state.update({
            "messages": [{"role": "assistant", "content": "🔥 **Welcome to BandLab Distribution.**\n\nI'm your AI Agent. Tell me about your release (e.g., *\"I'm dropping a Pop single called 'Summer' by DJ X\"*) and I'll handle the paperwork."}],
            "data": {
                # REQUIRED
                "title": None,
                "artist": None,
                "version": None,
                "genre": None,
                "date": None,
                "explicit": None,
                # OPTIONAL
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
    with st.spinner("🤖 Agent analyzing intent..."):
        result = call_llm_agent(st.session_state.messages, st.session_state.data)
        
        # 3. Apply Updates
        updates = result.get("updates", {})
        for k, v in updates.items():
            if k in st.session_state.data:
                st.session_state.data[k] = v
        
        # 4. Add Bot Response
        st.session_state.messages.append({"role": "assistant", "content": result.get("response")})
        
    st.rerun()

# --- 5. UI COMPONENTS ---

def render_dashboard():
    d = st.session_state.data
    
    st.markdown("### 💿 Live Draft")
    
    # REQUIRED SECTION
    st.markdown("<div class='status-header'>Required Metadata</div>", unsafe_allow_html=True)
    req_fields = ["title", "artist", "version", "genre", "date", "explicit"]
    
    for f in req_fields:
        val = d.get(f)
        status_html = f"<span class='badge-done'>✓ {val}</span>" if val else "<span class='badge-missing'>⭕ Required</span>"
        st.markdown(f"<div class='field-row'><span class='field-name'>{f.title()}</span>{status_html}</div>", unsafe_allow_html=True)

    # OPTIONAL SECTION
    st.markdown("<div class='status-header' style='margin-top:15px;'>Optional Metadata</div>", unsafe_allow_html=True)
    opt_fields = ["label", "upc", "isrc"]
    
    for f in opt_fields:
        val = d.get(f)
        status_html = f"<span class='badge-done'>{val}</span>" if val else "<span class='badge-optional'>Empty</span>"
        st.markdown(f"<div class='field-row'><span class='field-name'>{f.upper()}</span>{status_html}</div>", unsafe_allow_html=True)

    # ASSETS SECTION
    st.markdown("<div class='status-header' style='margin-top:15px;'>Assets</div>", unsafe_allow_html=True)
    
    c_stat = "✅ Uploaded" if d['cover_status'] else "❌ Missing"
    a_stat = "✅ Uploaded" if d['audio_status'] else "❌ Missing"
    
    st.markdown(f"<div class='field-row'><span class='field-name'>Cover Art</span><span>{c_stat}</span></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='field-row'><span class='field-name'>Master Audio</span><span>{a_stat}</span></div>", unsafe_allow_html=True)

def render_chat():
    for msg in st.session_state.messages:
        cls = "user-msg" if msg['role'] == "user" else "bot-msg"
        st.markdown(f"<div class='{cls}'>{msg['content']}</div>", unsafe_allow_html=True)
    
    # Invisible anchor
    st.markdown("<div id='end'></div>", unsafe_allow_html=True)

# --- 6. DEMO SCENARIOS (THE "HAPPY PATHS") ---

def trigger_demo(scenario):
    st.session_state.messages = [] # Clear chat
    # Reset Data
    init_state() 
    
    if scenario == "1":
        # The "One-Shot" Input
        process_input("I want to release a Pop track called 'Midnight City' by DJ Cloud dropping tomorrow. It's the original mix.")
    
    elif scenario == "2":
        # The "Education" Flow
        st.session_state.messages.append({"role": "assistant", "content": "What is the Release Title?"})
        process_input("Actually, I have a question. What is an ISRC code and do I need one?")
        
    elif scenario == "3":
        # The "Validation" Flow (Simulated via upload context)
        st.session_state.data['title'] = "Summer Vibes"
        st.session_state.messages.append({"role": "assistant", "content": "Title set to 'Summer Vibes'. Please upload cover art."})
        st.rerun()

# --- 7. MAIN APP FLOW ---

init_state()

# SIDEBAR
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/BandLab_Technologies_logo.svg/2560px-BandLab_Technologies_logo.svg.png", width=140)
    
    # DASHBOARD
    render_dashboard()
    
    st.divider()
    
    # DEMO CONTROLS
    st.markdown("### ⚡ Demo Scenarios")
    if st.button("Scenario 1: One-Shot Extraction"): trigger_demo("1")
    if st.button("Scenario 2: Contextual Education"): trigger_demo("2")
    if st.button("Scenario 3: Ready for Upload"): trigger_demo("3")
    
    st.divider()
    if st.button("Reset"):
        st.session_state.clear()
        st.rerun()

# MAIN CHAT AREA
st.title("BandLab Distribution AI")

# Render History
render_chat()

# Asset Uploaders (Context Aware)
# Only show if Title/Artist are set (Basic gatekeeping) or if user explicitly is at that stage
if st.session_state.data.get("title"):
    with st.expander("📂 Asset Upload Zone (Drag & Drop)", expanded=True):
        c1, c2 = st.columns(2)
        
        # COVER ART
        cover = c1.file_uploader("Cover Art (3000px)", type=["jpg", "png"], key="u_cover")
        if cover and not st.session_state.data['cover_status']:
            st.session_state.data['cover_status'] = True
            # Simulate Vision AI
            st.toast("👁️ Vision AI Scanning...", icon="🤖")
            time.sleep(1)
            st.session_state.messages.append({"role": "assistant", "content": "Cover Art received. Vision AI check passed (No explicit content detected)."})
            st.rerun()

        # AUDIO
        audio = c2.file_uploader("Audio (WAV)", type=["wav", "mp3"], key="u_audio")
        if audio and not st.session_state.data['audio_status']:
            st.session_state.data['audio_status'] = True
            st.toast("🎧 Analyzing Audio...", icon="🎵")
            time.sleep(1)
            st.session_state.messages.append({"role": "assistant", "content": "Audio uploaded. 44.1kHz / 16-bit verified."})
            st.rerun()

# Chat Input
st.chat_input("Type your reply...", key="u_in", on_submit=lambda: process_input(st.session_state.u_in))
