from utils import send_job_notification  # 'f' small kar diya hai
import requests
from flask import Flask, render_template, request, jsonify
import os, json

app = Flask(__name__)

# API Keys (Updated with your new key)
SERPER_API_KEY = "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d"
GEMINI_API_KEY = "AIzaSyDxIVi8NxFf5QEGoXb2wT1FRbzyKqfHKf0" # Nayi Key add ho gayi
CURRENT_APP_VERSION = "2.7"

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
        q_text = data.get('interest', 'latest jobs')
        query = f"{q_text} official recruitment portal 2026"
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        response = requests.post('https://google.serper.dev/search', headers=headers, json={'q': query, 'num': 40})
        return jsonify(response.json().get('organic', []))
    except: 
        return jsonify([])

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        name = data.get('name', 'User')
        message = data.get('message', '')
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        prompt = f"You are Rozgar AI by R YADAV PRODUCTION. User {name} is asking: {message}. Answer in a helpful way."
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        # Timeout ko 30 kar diya taaki network error kam aaye
        res = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload), timeout=30)
        
        res_json = res.json()
        
        if 'candidates' in res_json:
            reply = res_json['candidates'][0]['content']['parts'][0]['text']
            return jsonify({"reply": reply})
        else:
            return jsonify({"reply": "AI is updating, please try again in a moment."})
            
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"reply": "Network error, please check your connection and try again!"})

if __name__ == '__main__':
    # Render ya local host dono pe chalega
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
