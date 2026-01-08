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

# --- 2. CONFIGURATION ---
st.set_page_config(page_title="BandLab AI Agent", page_icon="🔥", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; color: #333; font-family: -apple-system, sans-serif; }
    
    /* CHAT STYLING */
    .user-bubble {
        background: #F50000; color: white; padding: 10px 15px; border-radius: 18px 18px 0 18px;
        margin: 5px 0 5px auto; max-width: 80%; width: fit-content;
        box-shadow: 0 2px 5px rgba(245,0,0,0.2);
    }
    .bot-bubble {
        background: #F3F4F6; color: #1F2937; padding: 10px 15px; border-radius: 18px 18px 18px 0;
        margin: 5px auto 5px 0; max-width: 80%; width: fit-content;
        border: 1px solid #E5E7EB;
    }
    
    /* DASHBOARD (SIDEBAR) */
    .draft-box {
        padding: 10px; background: #fafafa; border-radius: 8px; margin-bottom: 5px;
        border: 1px solid #eee; font-size: 0.9em; display: flex; justify-content: space-between;
    }
    .missing { color: #F50000; font-weight: bold; }
    .filled { color: #10B981; font-weight: bold; }
    
    /* HIDE STREAMLIT UI */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 3. THE LLM BRAIN (INTENT & EXTRACTION) ---

def call_llm(messages, model_type="auto"):
    """
    Sends chat history to LLM. 
    Returns the raw text response.
    """
    # System Prompt: Defines the persona and the goal
    system_prompt = """
    You are 'DistroBot', an expert A&R Agent for BandLab.
    Your goal is to help the user prepare a music release (Single/Album) for Spotify.
    
    Current Draft State: {current_state}
    
    YOUR RESPONSIBILITIES:
    1. EXTRACT METADATA: If the user provides info (Title, Artist, Genre, etc.), update the JSON state.
    2. VALIDATE: If the user uploads art with text that doesn't match the title, warn them.
    3. EDUCATE: If the user asks "What is ISRC?", explain it simply.
    4. GUIDE: Look at the 'Current Draft State'. Ask for the NEXT missing field politely.
       - Order of importance: Title -> Artist -> Version -> Genre -> Date -> Label -> Cover Art -> Audio.
    5. STYLE: Be casual, encouraging, and concise. Like a helpful studio engineer.
    
    OUTPUT FORMAT:
    You must output a JSON object containing TWO keys:
    1. "response": The text reply to the user.
    2. "updates": A dictionary of fields to update (e.g., {"title": "Summer Vibes", "artist": "DJ Cloud"}). If no updates, return {}.
    
    EXAMPLE INPUT: "My song is called Midnight Coffee"
    EXAMPLE OUTPUT:
    {
      "response": "Love that title! Is 'Midnight Coffee' a Single or part of an EP?",
      "updates": {"title": "Midnight Coffee"}
    }
    """
    
    # Inject current state into prompt
    state_str = json.dumps(st.session_state.data)
    sys_prompt_fmt = system_prompt.replace("{current_state}", state_str)
    
    # 1. GROQ (Fastest)
    if "GROQ_API_KEY" in st.secrets:
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            # Format history for API
            api_msgs = [{"role": "system", "content": sys_prompt_fmt}]
            for m in messages:
                api_msgs.append({"role": m["role"], "content": m["content"]})
                
            res = client.chat.completions.create(
                messages=api_msgs,
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"} # Force JSON
            )
            return res.choices[0].message.content
        except Exception as e:
            print(f"Groq Error: {e}")

    # 2. OPENAI (Backup)
    if "OPENAI_API_KEY" in st.secrets:
        try:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            api_msgs = [{"role": "system", "content": sys_prompt_fmt}]
            for m in messages:
                api_msgs.append({"role": m["role"], "content": m["content"]})
                
            res = client.chat.completions.create(
                model="gpt-4o",
                messages=api_msgs,
                response_format={"type": "json_object"}
            )
            return res.choices[0].message.content
        except: pass

    # Fallback if no keys
    return '{"response": "I am offline (Check API Keys).", "updates": {}}'

# --- 4. STATE MANAGEMENT ---

def init():
    if "messages" not in st.session_state:
        st.session_state.update({
            "messages": [
                {"role": "assistant", "content": "👋 Hi! I'm your BandLab Release Agent.\n\nTell me about your new track. What's the title and genre?"}
            ],
            "data": {
                "title": None,
                "artist": None,
                "version": None,
                "genre": None,
                "date": None,
                "upc": None,
                "isrc": None,
                "label": None,
                "cover_status": "Missing",
                "audio_status": "Missing"
            },
            "processing": False
        })

def process_user_input():
    user_text = st.session_state.user_input
    if not user_text: return

    # 1. Add User Message
    st.session_state.messages.append({"role": "user", "content": user_text})
    st.session_state.processing = True

def run_agent_logic():
    if st.session_state.processing:
        # 1. Call LLM with History
        raw_json = call_llm(st.session_state.messages)
        
        try:
            # 2. Parse JSON
            parsed = json.loads(raw_json)
            bot_reply = parsed.get("response", "I didn't quite catch that.")
            updates = parsed.get("updates", {})
            
            # 3. Update State (The "Extraction" Magic)
            for key, val in updates.items():
                # Normalize keys to match our data structure
                if key in st.session_state.data:
                    st.session_state.data[key] = val
            
            # 4. Add Bot Message
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            
        except:
            st.session_state.messages.append({"role": "assistant", "content": "⚠️ Error parsing AI response."})
        
        st.session_state.processing = False
        st.rerun()

# --- 5. UI COMPONENTS ---

def render_chat():
    for msg in st.session_state.messages:
        if msg['role'] == "user":
            st.markdown(f"<div class='user-bubble'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='bot-bubble'>{msg['content']}</div>", unsafe_allow_html=True)
    
    # Invisible div to anchor scroll (optional hack)
    st.markdown("<div id='end-of-chat'></div>", unsafe_allow_html=True)

def render_dashboard():
    st.markdown("### 💿 Live Draft")
    d = st.session_state.data
    
    # Render Fields with Visual Status
    fields = ["title", "artist", "genre", "version", "date", "label"]
    for f in fields:
        val = d.get(f)
        status = "filled" if val else "missing"
        val_display = val if val else "Required"
        
        st.markdown(f"""
        <div class="draft-box">
            <span>{f.title()}</span>
            <span class="{status}">{val_display}</span>
        </div>
        """, unsafe_allow_html=True)
        
    st.divider()
    
    # Asset Status
    c1, c2 = st.columns(2)
    c1.metric("Cover Art", "✅" if d['cover_status'] == "Uploaded" else "❌")
    c2.metric("Audio", "✅" if d['audio_status'] == "Uploaded" else "❌")
    
    st.divider()
    if st.button("🔴 Hard Reset"):
        st.session_state.clear()
        st.rerun()

# --- 6. MOCK FILE HANDLERS (Simulated AI Vision/Audio) ---

def handle_uploads():
    # Only show uploader if bot asks for it or context implies it
    # For this demo, we put it in the sidebar or an expander to keep chat clean
    with st.expander("📂 Asset Upload Zone (Drag & Drop)"):
        cover = st.file_uploader("Cover Art", type=["jpg", "png"], key="u_cover")
        if cover and st.session_state.data['cover_status'] == "Missing":
            st.session_state.data['cover_status'] = "Uploaded"
            # Simulate Vision AI Catching Mismatch
            current_title = st.session_state.data.get('title', '')
            if current_title and "Summer" not in current_title: 
                # Inject a system event to force the bot to react
                st.session_state.messages.append({
                    "role": "system", 
                    "content": f"SYSTEM EVENT: User uploaded cover art. Vision AI detected text 'Summer Vibes', but Draft Title is '{current_title}'. Mismatch detected."
                })
                st.session_state.processing = True
                st.rerun()
            else:
                st.session_state.messages.append({"role": "system", "content": "SYSTEM EVENT: Cover art uploaded successfully. No text issues."})
                st.session_state.processing = True
                st.rerun()

        audio = st.file_uploader("Audio File", type=["wav", "mp3"], key="u_audio")
        if audio and st.session_state.data['audio_status'] == "Missing":
            st.session_state.data['audio_status'] = "Uploaded"
            st.session_state.messages.append({"role": "system", "content": "SYSTEM EVENT: Audio uploaded. Tech check passed (44.1kHz)."})
            st.session_state.processing = True
            st.rerun()

# --- 7. MAIN APP FLOW ---

init()

# SIDEBAR DASHBOARD
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/BandLab_Technologies_logo.svg/2560px-BandLab_Technologies_logo.svg.png", width=140)
    render_dashboard()
    handle_uploads()

# MAIN CHAT
st.title("BandLab Distribution AI")
render_chat()

# INPUT AREA
if not st.session_state.processing:
    st.chat_input("Type your reply...", key="user_input", on_submit=process_user_input)

# BACKGROUND LOGIC RUNNER
if st.session_state.processing:
    run_agent_logic()
