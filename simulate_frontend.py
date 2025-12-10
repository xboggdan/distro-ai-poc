import requests
import json

url = "http://127.0.0.1:5000/chat"

# 1. SETUP: We simulate a user named xboggdan who DOES NOT have a payout method yet
context = {
    "artistName": "xboggdan",
    "hasPayoutMethod": False 
}

history = []

while True:
    user_input = input("\nYou: ")
    
    payload = {
        "message": user_input,
        "history": history,
        "userContext": context
    }
    
    response = requests.post(url, json=payload).json()
    
    # Print AI Response
    print(f"🤖 AI: {response['text']}")
    
    # Check if AI updated the form
    if response.get('functionCall'):
        print(f"📝 FORM UPDATE: {json.dumps(response['functionCall']['args'], indent=2)}")

    # Update history
    history.append({"role": "user", "text": user_input})
    history.append({"role": "model", "text": response['text']})