from utils import send_job_notification 
import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS 
from flask_caching import Cache 
import os, json

app = Flask(__name__)
CORS(app)

# Cache Setup: Performance boost ke liye (10 min timeout)
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 600})

# API Keys
SERPER_API_KEY = "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d"
GEMINI_API_KEY = "AIzaSyDxIVi8NxFf5QEGoXb2wT1FRbzyKqfHKf0" 
CURRENT_APP_VERSION = "3.1" # Naya Version

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
        
        # PRO AGGREGATOR LOGIC: 
        # Agar query mein 'govt' ya 'sarkari' hai toh ye sites target hongi
        if "govt" in q_text.lower() or "sarkari" in q_text.lower() or "railway" in q_text.lower():
            smart_query = f"{q_text} (site:sarkariresult.com OR site:freejobalert.com OR site:ssc.nic.in) 2026"
        # Agar Private/WFH hai toh LinkedIn aur Naukri target honge
        else:
            smart_query = (
                f"{q_text} (site:naukri.com OR site:linkedin.com/jobs OR "
                f"site:internshala.com OR site:indeed.com) "
                f"work from home remote 2026"
            )
        
        headers = {
            'X-API-KEY': SERPER_API_KEY, 
            'Content-Type': 'application/json'
        }
        
        # 40 results taaki variety bani rahe
        response = requests.post(
            'https://google.serper.dev/search', 
            headers=headers, 
            json={'q': smart_query, 'num': 40}, 
            timeout=20
        )
        
        results = response.json().get('organic', [])

        # Backup: Agar results kam milti hain toh generic search mix karega
        if len(results) < 8:
            backup_query = f"{q_text} vacancy 2026"
            res_backup = requests.post(
                'https://google.serper.dev/search', 
                headers=headers, 
                json={'q': backup_query, 'num': 20}, 
                timeout=15
            )
            results.extend(res_backup.json().get('organic', []))

        return jsonify(results)
    except Exception as e:
        print(f"Aggregator Error: {e}")
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
        User's Concern: {message}
        Goal: Provide job search tips (Govt/Private), career guidance, and motivation in friendly Hinglish.
        Explain WFH (Work from home) and Part-time benefits if asked.
        """
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        res = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload), timeout=30)
        res_json = res.json()
        
        if 'candidates' in res_json:
            reply = res_json['candidates'][0]['content']['parts'][0]['text']
            return jsonify({"reply": reply})
        else:
            return jsonify({"reply": "Bhai, AI server thoda slow hai, ek baar phir se koshish karein!"})
            
    except Exception as e:
        return jsonify({"reply": "Network issue! Kripya internet check karein."})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
