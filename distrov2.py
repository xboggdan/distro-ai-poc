import streamlit as st
import json
import time

# --- 1. THE BRAIN (SYSTEM PROMPT) ---
# This prompt is the single source of truth for the AI's behavior.
# It includes the specific validation rules from your document.

AGENT_SYSTEM_PROMPT = """
You are **DistroBot**, a highly specialized A&R Compliance Agent for BandLab.
Your goal is to guide the user through a Single Release submission, ensuring every field adheres to strict DSP (Spotify/Apple) metadata standards.

### 1. CORE BEHAVIOR & TONE
* **Role:** You are an expert consultant, not just a form filler.
* **Tone:** Professional, encouraging, but strict on compliance.
* **Method:** Ask for information conversationally. If the user provides invalid data (e.g., a one-word Composer name), **reject it politely**, explain WHY (DSP rules), and ask again.
* **Scope:** You are handling a **Single Release**.

### 2. DATA STRUCTURE (THE SOURCE OF TRUTH)
You are building this JSON object. Update it as you gather info.
{
  "release": {
    "title": null,      // Mandatory. No "feat", "prod", emojis.
    "version": {
        "type": null,   // From Fixed List. Default "Original".
        "custom_text": null, // Only if type="Other"
        "remaster_year": null, // Mandatory if type="Remastered"
        "remix_confirmed": false // Mandatory if type="Remix"
    },
    "artist": "xboggdan", // Pre-filled/Locked.
    "genre": null,      // Mandatory.
    "date": "ASAP",     // Mandatory.
    "label": null,      // Optional.
    "upc": null,        // Optional.
    "documentation": null // Optional (Proof of rights)
  },
  "track": {
    "title": null,      // Locked to Release Title for Singles.
    "is_cover": false,  // Logic check.
    "released_before": {
        "status": false,
        "original_year": null // Mandatory if status=true (1900 to current-1)
    },
    "credits": {
        "composers": [],   // Mandatory. LEGAL NAMES (First+Last).
        "artists": [       // Mandatory. Max 4.
            {"name": "xboggdan", "role": "Primary", "spotify_id": null, "apple_id": null}
        ],
        "performers": [],  // Mandatory. LEGAL NAMES + Instrument.
        "production": [],  // Mandatory. LEGAL NAMES + Role.
        "contributors": [] // Optional.
    },
    "lyrics": {
        "language": null,     // Mandatory. If "Instrumental", skip rest.
        "explicit_rating": null, // Mandatory if not Instrumental (Clean/Explicit/Non-Explicit).
        "lyricist": []        // Mandatory if not Instrumental. LEGAL NAMES.
    },
    "isrc": null,       // Optional.
    "publisher": null   // Optional.
  }
}

### [cite_start]3. VALIDATION RULES (STRICT ENFORCEMENT) [cite: 1, 14, 15]

#### **A. Names (Composers, Performers, Production, Lyricists, Contributors)**
* **Rule:** MUST be a **Legal Name** (First Name + Last Name).
* [cite_start]**Validation:** Reject inputs with only 1 word[cite: 37, 38].
* **Forbidden Chars:** `( ) { } [ ] \ / ! [cite_start]@ # $ % ^ & * + =`[cite: 37, 39, 42].
* [cite_start]**Forbidden Words:** "feat", "prod", "artist", "unknown", "beats"[cite: 38].

#### **B. Titles (Release/Track)**
* [cite_start]**Forbidden:** Emojis, "feat" (use artist field instead), "produced by", "Official"[cite: 13, 14, 17, 18].
* [cite_start]**Logic:** For a Single, Track Title MUST match Release Title[cite: 35, 36].
* you need to allow user to input 1 word in the release title if they want to because this is allowed. 
* 

#### **C. Version Logic (New Standard)**
* **Input:** User must choose from this list:
    * *Alternate Take, Instrumental, Radio Edit, Extended, Remastered, Sped Up, Slowed Down, Lo-Fi, Acapella, Acoustic, Deluxe, Demo, Freestyle, Karaoke, Live, Remix, Slowed and Reverb, Other.*
* **Conditionals:**
    * [cite_start]If **Remastered**: You MUST ask for the "Original Release Year" (1900-Present)[cite: 36].
    * If **Remix**: You MUST ask user to confirm: "Do you have the rights to remix this track?" (Checkbox logic).
    * If **Other**: Ask user to type the version (e.g., "Club Mix"). [cite_start]Validate forbidden words (no "Original", "Album", "Explicit")[cite: 37].

#### **D. "Released Before" Logic**
* Ask: "Has this track been released before?"
* [cite_start]If **Yes**: You MUST ask for the **Year of Original Recording** (Range: 1900 to Current Year - 1)[cite: 36].

#### **E. Lyrics & Explicit**
* Ask: "What is the language of the lyrics?" (Or "Is it Instrumental?") [cite_start][cite: 38].
* [cite_start]If **Instrumental**: Set `explicit_rating` = "Clean", `lyricist` = null[cite: 38].
* If **Language Selected**:
    1.  [cite_start]Ask: "Is the content Explicit, Clean, or Non-Explicit?" [cite: 38]
    2.  [cite_start]Ask: "Who is the Lyricist? (Legal First & Last Name required)"[cite: 38].

### 4. CONVERSATIONAL FLOW (THE HAPPY PATH)

**Phase 1: Release Details**
1.  **Title:** "What is the name of your song?" (Validate).
2.  **Version:** "Is this the Original version, or a special version (like Remix, Live, etc.)?"
    * *Agent:* Present options. Handle conditionals (Year/Confirmation) immediately if triggered.
3.  [cite_start]**Genre:** "What is the primary genre?" [cite: 20]
4.  [cite_start]**Date:** "Releasing ASAP or a specific date?" [cite: 20]
5.  [cite_start]**Label/UPC:** "Do you have a Label or UPC, or should we auto-generate?" [cite: 21]

**Phase 2: Track & Credits (The Complex Part)**
1.  [cite_start]**Composers:** "Who wrote the song? I need **Legal First and Last Names** for publishing rights." [cite: 37]
    * *Suggestion:* "Is it just you (Bogdan Hershall)?"
2.  [cite_start]**Artists:** "You are the Main Artist. Any featured artists?" [cite: 17]
    * *Limit:* Max 4 Primary. Ask for Role (Primary/Feature) for new adds.
3.  [cite_start]**Performers (Mandatory):** "Who played instruments or sang? (Legal Name + Instrument)." [cite: 42]
    * *Validation:* Reject 1-word names.
4.  [cite_start]**Production (Mandatory):** "Who produced/mixed/mastered? (Legal Name + Role)." [cite: 42]
    * *Validation:* Reject 1-word names.
5.  **History:** "Has this been released before?" (Handle Year logic).
6.  **Lyrics:** "What language are the lyrics in?" (Handle Explicit/Lyricist logic).

### 5. OUTPUT INSTRUCTIONS
Always reply with a JSON object containing `response` (text to user) and `updates` (data to merge).
"""

# --- 2. SETUP & IMPORTS ---
try:
    from groq import Groq
    import google.generativeai as genai
    from openai import OpenAI
except ImportError:
    pass

st.set_page_config(page_title="BandLab Distro Agent", page_icon="🔥", layout="wide")

st.markdown("""
<style>
    /* BANDLAB STYLE OVERRIDES */
    .stApp { background-color: #FFFFFF; color: #333333; font-family: -apple-system, sans-serif; }
    .user-msg { background-color: #F50000; color: white; padding: 12px 18px; border-radius: 18px 18px 0 18px; margin: 8px 0 8px auto; max-width: 75%; box-shadow: 0 2px 6px rgba(245,0,0,0.2); }
    .bot-msg { background-color: #F3F4F6; color: #1F2937; padding: 12px 18px; border-radius: 18px 18px 18px 0; margin: 8px auto 8px 0; max-width: 75%; border: 1px solid #E5E7EB; }
    .field-row { display: flex; justify-content: space-between; align-items: center; padding: 8px; background: #FAFAFA; border-bottom: 1px solid #eee; font-size: 0.9em; }
    .badge-req { color: #DC2626; font-weight: 700; } 
    .badge-done { color: #059669; font-weight: 700; }
    .big-btn > button { background-color: #F50000; color: white; font-weight: 600; padding: 12px; width: 100%; border-radius: 8px; border:none; }
    .big-btn > button:hover { background-color: #d10000; }
</style>
""", unsafe_allow_html=True)

# --- 3. AGENT LOGIC ---

def call_llm(messages, current_data):
    # INJECT STATE INTO THE GOD PROMPT
    final_prompt = AGENT_SYSTEM_PROMPT.replace("{current_state}", json.dumps(current_data, indent=2))
    
    try:
        # 1. GROQ
        if "GROQ_API_KEY" in st.secrets:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"])
            msgs = [{"role": "system", "content": final_prompt}] + [{"role": m["role"], "content": m["content"]} for m in messages]
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=msgs, response_format={"type": "json_object"})
            return json.loads(res.choices[0].message.content)
            
        # 2. GEMINI
        elif "GEMINI_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
            chat = model.start_chat(history=[])
            prompt_payload = final_prompt + f"\n\nLATEST USER MESSAGE: {messages[-1]['content']}"
            res = chat.send_message(prompt_payload)
            return json.loads(res.text)

        # 3. OPENAI
        elif "OPENAI_API_KEY" in st.secrets:
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            msgs = [{"role": "system", "content": final_prompt}] + [{"role": m["role"], "content": m["content"]} for m in messages]
            res = client.chat.completions.create(model="gpt-4o", messages=msgs, response_format={"type": "json_object"})
            return json.loads(res.choices[0].message.content)

    except Exception as e:
        return {"response": f"❌ Agent Error: {str(e)}", "updates": {}}

    # Fallback for Demo Mode (No Keys)
    return mock_logic(messages[-1]['content'])

def mock_logic(text):
    text = text.lower()
    updates = {}
    
    # Validation Mock: Composer Name
    if "composer" in text or "wrote" in text:
        # Check if user provided 2 words
        if len(text.split()) < 3 and "i did" not in text: # simple heuristic
            return {
                "response": "I need the **Legal First and Last Name** for the composer (e.g. 'John Doe'). Single names are not accepted for publishing.",
                "updates": {}
            }
        updates["track"] = {"credits": {"composers": ["Mock Composer"]}}

    # Version Logic Mock
    if "remastered" in text:
        return {
            "response": "Since this is **Remastered**, what was the **Year of the Original Release**? (1900-2025)",
            "updates": {"release": {"version": {"type": "Remastered"}}}
        }
    
    if "1999" in text: # answering the year question
        updates["release"] = {"version": {"remaster_year": 1999}}
        return {
            "response": "Got it. Original release 1999. Moving on...",
            "updates": updates
        }

    # "Solo Artist" Shortcut Mock
    if "i did everything" in text or "i did all" in text:
        credits = {
            "composers": ["Bogdan Hershall"],
            "performers": [{"name": "Bogdan Hershall", "role": "Vocals"}],
            "production": [{"name": "Bogdan Hershall", "role": "Producer"}]
        }
        return {
            "response": "Understood. I've set **Bogdan Hershall** as the Composer, Performer, and Producer. \n\nIs the track **Instrumental** or does it have lyrics?",
            "updates": {"track": {"credits": credits}}
        }
        
    # Standard field extraction mocks
    if "title" in text: updates["release"] = {"title": "Mock Title"}
    if "hip hop" in text: updates["release"] = {"genre": "Hip Hop"}
    
    # Chaos Artist Mock
    if "chaos" in text:
        return {
            "response": "Chaos input parsed! I found Title, Genre, and Date.", 
            "updates": {"release": {"title": "Chaos Theory", "genre": "Hyperpop", "date": "Friday"}}
        }
        
    return {"response": "I am in Offline/Demo Mode. Try saying 'I did everything' or 'Remastered' to test logic.", "updates": updates}

# --- 4. APP LOGIC ---

def init_state():
    if "messages" not in st.session_state:
        st.session_state.update({
            "messages": [],
            "data": {
                "release": {
                    "title": None, "version": {"type": "Original"}, 
                    "artist": "xboggdan", "genre": None, "date": None
                },
                "track": {
                    "credits": {"composers": [], "performers": [], "production": []},
                    "lyrics": {"explicit_rating": None},
                    "released_before": {"status": False}
                },
                "assets": {"cover_status": False, "audio_status": False}
            }
        })

def process_input(user_txt):
    if not user_txt: return
    st.session_state.messages.append({"role": "user", "content": user_txt})
    
    with st.spinner("🤖 Agent Thinking..."):
        result = call_llm(st.session_state.messages, st.session_state.data)
        
        # Recursive Update Function
        def update_nested(d, u):
            for k, v in u.items():
                if isinstance(v, dict):
                    d[k] = update_nested(d.get(k, {}), v)
                else:
                    d[k] = v
            return d

        update_nested(st.session_state.data, result.get("updates", {}))
                    
        st.session_state.messages.append({"role": "assistant", "content": result.get("response")})
    st.rerun()

# --- 5. RENDER UI ---

init_state()

# SIDEBAR DASHBOARD
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/BandLab_Technologies_logo.svg/2560px-BandLab_Technologies_logo.svg.png", width=140)
    d = st.session_state.data
    
    st.markdown("### 💿 Live Metadata Draft")
    
    # Helper to render row
    def row(lbl, val, req=True):
        status = "✅" if val else ("⭕ Req" if req else "Optional")
        if isinstance(val, list): status = f"✅ {len(val)}" if val else ("⭕ Req" if req else "Optional")
        st.markdown(f"<div class='field-row'><b>{lbl}</b> <span>{status}</span></div>", unsafe_allow_html=True)

    st.caption("RELEASE")
    r = d.get('release', {})
    row("Title", r.get('title')); row("Artist", r.get('artist')); row("Genre", r.get('genre'))
    
    st.caption("CREDITS")
    t = d.get('track', {}).get('credits', {})
    row("Composers", t.get('composers')); row("Producers", t.get('production'))
    
    st.caption("ASSETS")
    a = d.get('assets', {})
    row("Cover Art", a.get('cover_status')); row("Audio", a.get('audio_status'))

    st.divider()
    # DEMO BUTTONS
    st.markdown("### ⚡ Demo Scenarios")
    
    def run_demo(scen_id):
        st.session_state.messages = []
        init_state()
        if scen_id == 1:
            process_input("I'm releasing a Hip Hop single called 'Empire' by xboggdan dropping ASAP.")
        elif scen_id == 2:
            st.session_state.data['release'].update({"title": "Neon", "genre": "Pop"})
            st.session_state.messages.append({"role": "assistant", "content": "Title: Neon. Genre: Pop. Who worked on this?"})
            process_input("I did everything myself.")
        elif scen_id == 3: # Education
            st.session_state.messages.append({"role": "assistant", "content": "What is the Release Title?"})
            process_input("Wait, what is an ISRC? Do I need one?")
        elif scen_id == 4: # Chaos
             process_input("yo song is 'Pizza' genre hyperpop i wrote it with mom but produced alone dropping friday")
        elif scen_id == 5: # Version Logic
             st.session_state.data['release'].update({"title": "Old Song"})
             st.session_state.messages.append({"role": "assistant", "content": "Title set. Is this the Original version?"})
             process_input("No, it's Remastered.")

        st.rerun()

    if st.button("1. One-Shot Entry"): run_demo(1)
    if st.button("2. Solo Artist Shortcut"): run_demo(2)
    if st.button("3. Educational Pivot"): run_demo(3)
    if st.button("4. Chaos Input"): run_demo(4)
    if st.button("5. Version Logic Check"): run_demo(5)
    if st.button("Reset"): st.session_state.clear(); st.rerun()

# MAIN SCREEN
st.title("BandLab Distribution AI")

if not st.session_state.messages:
    # WELCOME SCREEN
    st.markdown("""
    <div style="text-align:center; padding: 40px; background: #F9FAFB; border-radius: 12px; margin-bottom: 20px;">
        <h2>👋 Hello, Artist.</h2>
        <p style="color:#666;">I'm your AI Distribution Agent. You can speak naturally.</p>
        <p><i>"I want to release a Pop song called 'Summer'..."</i></p>
    </div>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown('<div class="big-btn">', unsafe_allow_html=True)
        if st.button("Start New Release"):
            st.session_state.messages.append({"role": "assistant", "content": "Let's get started! What is the **Release Title**?"})
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # CHAT SCREEN
    for msg in st.session_state.messages:
        cls = "user-msg" if msg['role'] == "user" else "bot-msg"
        st.markdown(f"<div class='{cls}'>{msg['content']}</div>", unsafe_allow_html=True)

# CHAT INPUT
st.chat_input("Type here...", key="u_in", on_submit=lambda: process_input(st.session_state.u_in))

