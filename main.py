import requests
from flask import Flask, render_template, request, jsonify
import os
import json

app = Flask(__name__)

# API KEYS
SERPER_API_KEY = "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d"
GEMINI_API_KEY = "AIzaSyC7BwdOrEM38fRsrR3rZzejwbBh7UpOinE"
CURRENT_APP_VERSION = "2.0" 

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
        
        # Strict Official Filters
        exclude = "-site:facebook.com -site:instagram.com -site:twitter.com -site:youtube.com -site:shiksha.com -site:testbook.com"
        official_filter = "(site:.gov.in OR site:.nic.in OR site:.edu OR site:org.in)"

        if job_type == 'results':
            query = f"{interest} official exam result 2025 2026 {official_filter} {exclude}"
        else:
            query = f"{interest} latest vacancy {state} 2026 {official_filter} {exclude}"
            
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        response = requests.post('https://google.serper.dev/search', headers=headers, json={'q': query, 'num': 10})
        return jsonify(response.json().get('organic', []))
    except:
        return jsonify([])

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_msg = data.get('message', '')
        u_name = data.get('name', 'Bhai')
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        # System Instructions for Study Plan & Branding
        prompt = f"""
        You are Rozgar AI, a professional career coach created by R YADAV PRODUCTION (Rahul Raj from Arwal, Bihar).
        User Name: {u_name}
        Task: 
        1. If user asks for a 'Study Plan' or 'Routine' for any hours (e.g., 5, 6, 8 hours), create a detailed hour-by-hour table.
        2. Focus heavily on Mathematics and Reasoning as per Rahul Raj's guidance.
        3. Always be respectful and talk like a helpful elder brother.
        4. Use a mix of Hindi and English.
        User Question: {user_msg}
        """
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        headers = {'Content-Type': 'application/json'}
        res = requests.post(url, headers=headers, data=json.dumps(payload))
        ai_reply = res.json()['candidates'][0]['content']['parts'][0]['text']
        return jsonify({"reply": ai_reply})
    except:
        return jsonify({"reply": "Bhai, server thoda busy hai. API key check karein!"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)