import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv('creds.env') # Loading your specific env file
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("Searching for available models...")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"- {m.name}")