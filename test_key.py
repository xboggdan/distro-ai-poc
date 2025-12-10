import os
import google.generativeai as genai
from dotenv import load_dotenv

# --- THE CHANGE IS HERE ---
# We tell it specifically to look for 'creds.env'
load_dotenv('creds.env') 

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: Could not find GEMINI_API_KEY in 'creds.env'.")
    print("   Make sure the file is in the same folder as this script!")
else:
    print(f"✅ Found API Key: {api_key[:10]}...") 

    try:
        genai.configure(api_key=api_key)
        # In test_key.py
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Say 'Hello from Google!' if you can hear me.")
        print(f"🤖 AI Response: {response.text}")
        print("🎉 SUCCESS! Your API key is working.")
    except Exception as e:
        print(f"❌ API Error: {e}")