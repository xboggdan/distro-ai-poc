import os
import time
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from google.api_core import exceptions

# 1. SETUP & AUTH
# Load the 'creds.env' file specifically
load_dotenv('creds.env')
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("No API Key found. Please check your creds.env file.")

genai.configure(api_key=api_key)

app = Flask(__name__)
CORS(app)  # Enables the frontend to talk to this backend

# 2. DEFINE THE DATA STRUCTURE (The Form Fields)
release_tool = {
    "function_declarations": [
        {
            "name": "update_release_draft",
            "description": "Saves the music release data into the form.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    # Screen 1: Basic Info
                    "release_title": { "type": "STRING", "description": "Title of single/album. No 'feat.' here." },
                    "genre": { "type": "STRING", "description": "Standard DSP genre" },
                    "version": { "type": "STRING", "description": "e.g., Live, Remix, Acoustic" },
                    "release_date_mode": { "type": "STRING", "enum": ["ASAP", "SPECIFIC"] },
                    "specific_date": { "type": "STRING", "description": "YYYY-MM-DD" },
                    
                    # Screen 2: Track Details
                    "composers": { 
                        "type": "ARRAY", 
                        "items": { "type": "STRING" },
                        "description": "Full legal names (First Last) only."
                    },
                    "is_explicit": { "type": "BOOLEAN" },
                    "language": { "type": "STRING" },
                    
                    # Screen 3: Assets (Flags only)
                    "artwork_uploaded": { "type": "BOOLEAN" },
                    "audio_uploaded": { "type": "BOOLEAN" }
                },
                "required": ["release_title", "genre"]
            }
        }
    ]
}

# 3. INITIALIZE THE MODEL
# We use gemini-2.5-flash because you confirmed it works and has quota.
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    tools=[release_tool]
)

@app.route('/chat', methods=['POST'])
def chat_agent():
    try:
        # Get data from Frontend/Simulation
        data = request.json
        user_message = data.get('message')
        history = data.get('history', [])
        user_context = data.get('userContext', {})

        # 4. DYNAMIC SYSTEM INSTRUCTION (The Brain)
        system_instruction = f"""
        ROLE: You are the BandLab Release Assistant.
        
        CURRENT CONTEXT:
        - Main Artist Name: "xboggdan" (LOCKED).
        - Payout Connected: {user_context.get('hasPayoutMethod', True)}
        
        CRITICAL RULES (Follow Strictly):
        1. **PAYOUT GATE**: If 'Payout Connected' is False, STOP IMMEDIATELY. 
           Say: "I see you don't have a payout method connected. You must connect Stripe or PayPal to proceed."
           Do NOT ask for track details until this is resolved.
           
        2. **TITLE CLEANUP**: If user says "Title is Road Home feat. Drake", REMOVE "feat. Drake" from the title. 
           Tell the user: "I moved Drake to the featured artist field to match DSP rules."
           
        3. **COMPOSER NAMES**: Enforce "First Last" legal names. If they say "Spitfire", ask for their real name.

        4. **FILE UPLOADS**: 
           - You cannot "see" files.
           - Wait for the system message: "[System: User uploaded file_name]"
           - Once received, confirm it and move to the next step.
           
        5. **ARTWORK CHECK**: Ask user to confirm the art has no text, URLs, or brands.

        YOUR GOAL: 
        Ask one question at a time. Call 'update_release_draft' tool to save data.
        """

        # 5. FORMAT HISTORY
        formatted_history = []
        for msg in history:
            role = "user" if msg['role'] == 'user' else "model"
            formatted_history.append({"role": role, "parts": [msg['text']]})

        # 6. START CHAT
        chat = model.start_chat(history=formatted_history)
        
        # Combine System Instruction + User Message
        full_prompt = f"SYSTEM INSTRUCTION: {system_instruction}\n\nUSER MESSAGE: {user_message}"

        # 7. RETRY LOGIC (The Fix for 'Try again in 1 min')
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = chat.send_message(full_prompt)
                
                # Check for Function Calls (Form Updates)
                function_call_data = None
                if response.parts:
                    for part in response.parts:
                        if fn := part.function_call:
                            function_call_data = {
                                "name": fn.name,
                                "args": dict(fn.args) 
                            }
                
                # Success! Return data.
                return jsonify({
                    "text": response.text,
                    "functionCall": function_call_data
                })

            except exceptions.ResourceExhausted:
                # This catches the 429 Rate Limit error
                wait_time = 30
                print(f"⚠️ Rate limit hit. Waiting {wait_time} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue  # Loop back and try again

            except Exception as e:
                # Other errors fail immediately
                print(f"❌ Error: {e}")
                return jsonify({"error": str(e)}), 500

        # If all retries fail
        return jsonify({"error": "Server is busy. Please try again in a moment."}), 429

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)