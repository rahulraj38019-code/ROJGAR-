from utils import send_job_notification 
import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS # Connectivity ke liye
from flask_caching import Cache # Speed ke liye
import os, json

app = Flask(__name__)
CORS(app)

# Cache Setup: 10 minute tak results save rahenge (App fast chalega)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 600})

# API Keys
SERPER_API_KEY = "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d"
GEMINI_API_KEY = "AIzaSyDxIVi8NxFf5QEGoXb2wT1FRbzyKqfHKf0" 
CURRENT_APP_VERSION = "2.9"

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/get_version', methods=['GET'])
def get_version(): 
    return jsonify({"version": CURRENT_APP_VERSION})

@app.route('/search', methods=['POST'])
@cache.cached(timeout=600, query_string=True)
def search():
    try:
        data = request.get_json()
        q_text = data.get('interest', 'latest jobs')
        
        # AGGREGATOR QUERY: Ye LinkedIn, Naukri aur Indeed se jobs dhundega
        # Agar user "ITI" search karega toh ye query banegi: "ITI jobs (site:naukri.com OR site:linkedin.com) 2026"
        smart_query = f"{q_text} (site:naukri.com OR site:linkedin.com OR site:indeed.com OR site:sarkariresult.com) 2026"
        
        headers = {
            'X-API-KEY': SERPER_API_KEY, 
            'Content-Type': 'application/json'
        }
        
        # Results limit 40 rakha hai taaki variety mile
        response = requests.post(
            'https://google.serper.dev/search', 
            headers=headers, 
            json={'q': smart_query, 'num': 40}, 
            timeout=20
        )
        
        results = response.json().get('organic', [])
        
        # Agar Aggregator se results kam aaye, toh ek simple search aur kar lega (Backup)
        if len(results) < 5:
            backup_query = f"{q_text} latest job openings 2026"
            res_backup = requests.post(
                'https://google.serper.dev/search', 
                headers=headers, 
                json={'q': backup_query, 'num': 20}, 
                timeout=15
            )
            results = res_backup.json().get('organic', [])

        return jsonify(results)
    except Exception as e:
        print(f"Search Error: {e}")
        return jsonify([])

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        name = data.get('name', 'Dost')
        message = data.get('message', '')
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        prompt = f"""
        You are Rozgar AI, a career expert by R YADAV PRODUCTION.
        User Name: {name}
        User Message: {message}
        Task: Help the user find jobs, career guidance, and success tips. 
        Use friendly Hinglish and be very professional yet supportive.
        """
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        res = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload), timeout=30)
        res_json = res.json()
        
        if 'candidates' in res_json:
            reply = res_json['candidates'][0]['content']['parts'][0]['text']
            return jsonify({"reply": reply})
        else:
            return jsonify({"reply": "Bhai, AI server thoda slow hai, ek baar phir se message bhejo!"})
            
    except Exception as e:
        print(f"Chat Error: {e}")
        return jsonify({"reply": "Network issue! Kripya internet check karein ya Render dashboard dekhein."})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
