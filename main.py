import requests
from flask import Flask, render_template, request, jsonify
import os, json

app = Flask(__name__)

# API Keys
SERPER_API_KEY = "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d"
GEMINI_API_KEY = "AIzaSyC7BwdOrEM38fRsrR3rZzejwbBh7UpOinE"
CURRENT_APP_VERSION = "2.7"

@app.route('/')
def index(): return render_template('index.html')

@app.route('/get_version', methods=['GET'])
def get_version(): return jsonify({"version": CURRENT_APP_VERSION})

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        q_text = data.get('interest', 'latest jobs')
        # Smart Query for More Results
        query = f"{q_text} official recruitment portal 2026"
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        response = requests.post('https://google.serper.dev/search', headers=headers, json={'q': query, 'num': 40})
        return jsonify(response.json().get('organic', []))
    except: return jsonify([])

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        prompt = f"You are Rozgar AI by R YADAV PRODUCTION. User {data.get('name')} is asking: {data.get('message')}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload), timeout=15)
        return jsonify({"reply": res.json()['candidates'][0]['content']['parts'][0]['text']})
    except: return jsonify({"reply": "Network error, try again!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))