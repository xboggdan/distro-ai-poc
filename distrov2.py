import streamlit as st
import time
import random

# --- CONFIGURATION ---
st.set_page_config(page_title="DistroBot V10.1", page_icon="💿", layout="wide")

# --- CSS FOR UI & TECH BADGES ---
st.markdown("""
<style>
    .stChatMessage {
        background-color: #f9f9f9;
        border-radius: 15px;
        padding: 10px;
        border: 1px solid #eee;
    }
    .tech-badge {
        font-size: 0.7em;
        color: #555;
        background-color: #e0e0e0;
        padding: 2px 8px;
        border-radius: 10px;
        margin-top: 6px;
        display: inline-block;
        font-family: monospace;
        border: 1px solid #ccc;
    }
    .badge-ai { background-color: #e3f2fd; color: #0d47a1; border-color: #90caf9; }
    .badge-logic { background-color: #fff3e0; color: #e65100; border-color: #ffcc80; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant", 
        "content": "Hello! I'm DistroBot V10. Let's get your music on Spotify. What is the **Release Title**?",
        "source": "Backend Logic",
        "model": "Hardcoded Init"
    }]
if "step" not in st.session_state:
    st.session_state.step = "title" 
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "mode" not in st.session_state:
    st.session_state.mode = "Distribution Flow"

# --- HELPER FUNCTIONS ---

def add_message(role, content, source="User Input", model="N/A"):
    st.session_state.messages.append({
        "role": role, 
        "content": content, 
        "source": source, 
        "model": model
    })

def simulate_ai_extraction(user_input):
    """
    Simulates extracting the core entity from a conversational sentence.
    """
    triggers = ["my title is", "release title is", "name is", "called", "track is"]
    cleaned = user_input
    
    # 1. AI Extraction Simulation
    lower_input = user_input.lower()
    detected = False
    for trigger in triggers:
        if trigger in lower_input:
            start_index = lower_input.find(trigger) + len(trigger)
            cleaned = user_input[start_index:].strip()
            cleaned = cleaned.strip('".')
            detected = True
            break
            
    if detected:
        return cleaned, "NLP Entity Extraction", "GPT-4o-Mini (Simulated)"
    else:
        return user_input.strip(), "Direct Input", "Rule-Engine v2"

def get_educational_response(query):
    """
    Simulates a RAG (Retrieval Augmented Generation) response.
    """
    query = query.lower()
    
    # Knowledge Base
    kb = {
        "royalties": "You keep 100% of your royalties. We do not take a cut. Payouts are monthly via PayPal.",
        "money": "You keep 100% of your royalties. We do not take a cut. Payouts are monthly via PayPal.",
        "membership": "No, you do not need a paid membership to distribute. Standard distribution is free.",
        "cost": "Distribution is free for standard releases.",
        "upc": "A UPC (Universal Product Code) is a unique barcode for your release. We generate one for you automatically for free.",
        "isrc": "ISRCs are unique codes for individual tracks. We assign these automatically if you don't have them.",
        "cover": "For cover songs, you must obtain a mechanical license. We can help you manage this via our partners.",
        "spotify": "Delivery to Spotify usually takes 24-48 hours after we approve your release.",
        "apple": "Apple Music ingestion can take up to
