import requests
from flask import Flask, render_template, request, jsonify
import os
import json

app = Flask(__name__)

# API KEYS
SERPER_API_KEY = "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d"
GEMINI_API_KEY = "AIzaSyC7BwdOrEM38fRsrR3rZzejwbBh7UpOinE"

# Server Version
CURRENT_APP_VERSION = "2.1" 

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
        interest = data.get('interest', 'latest jobs')
        state = data.get('state', 'India')
        job_type = data.get('type', 'all')
        official_filter = "(site:.gov.in OR site:.nic.in OR site:.edu OR site:org.in)"
        query = f"{interest} official 2026 {official_filter} -site:facebook.com"
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        response = requests.post('https://google.serper.dev/search', headers=headers, json={'q': query, 'num': 10})
        return jsonify(response.json().get('organic', []))
    except:
        return jsonify([])

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        # Papa wala special prompt instructions
        prompt = f"You are Rozgar AI by R YADAV PRODUCTION. Owner: Rahul Raj. Provide 6-hour study plans and job info respectfully: {data.get('message')}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        return jsonify({"reply": res.json()['candidates'][0]['content']['parts'][0]['text']})
    except:
        return jsonify({"reply": "Network issue hai bhai!"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)