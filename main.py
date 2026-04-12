import requests
from flask import Flask, render_template, request, jsonify
import os, json

app = Flask(__name__)

# Aapki API Keys (Inhe check kar lena ki sahi hain ya nahi)
SERPER_API_KEY = "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d"
GEMINI_API_KEY = "AIzaSyC7BwdOrEM38fRsrR3rZzejwbBh7UpOinE"

# Version ko 2.5 rakha hai taaki HTML se match kare
CURRENT_APP_VERSION = "2.5"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_version', methods=['GET'])
def get_version():
    return jsonify({"version": CURRENT_APP_VERSION})

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        q_text = data.get('interest', 'latest government jobs 2026')
        
        # Smart Search Query: Isse "No Results" wali problem solve ho jayegi
        # Humne 'official' aur 'recruitment' keywords jode hain safety ke liye
        query = f"{q_text} official recruitment portal 2026"
        
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        # num: 40 (Isse ek baar mein 40 jobs/results dikhenge)
        payload = {'q': query, 'num': 40}
        
        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        results = response.json().get('organic', [])
        
        return jsonify(results)
    except Exception as e:
        print(f"Search Error: {e}")
        return jsonify([])

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_msg = data.get('message')
        user_name = data.get('name', 'User')
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        # AI ko Rahul Raj ke brand ke hisab se train kiya gaya hai
        prompt = f"You are Rozgar AI, created by R YADAV PRODUCTION. Help {user_name} with their career. Context: {user_msg}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        res = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload), timeout=15)
        return jsonify({"reply": res.json()['candidates'][0]['content']['parts'][0]['text']})
    except Exception as e:
        print(f"Chat Error: {e}")
        return jsonify({"reply": "Bhai, server busy hai ya network slow hai. Ek baar phir try karo!"})

if __name__ == '__main__':
    # Render ya local host dono par chalega
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))