from utils import send_job_notification 
import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS 
from flask_caching import Cache 
import os, json

app = Flask(__name__)
CORS(app)

# Caching ko thoda flexible rakha hai taaki filters switch karne par turant naya data mile
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})

SERPER_API_KEY = "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d"
GEMINI_API_KEY = "AIzaSyDxIVi8NxFf5QEGoXb2wT1FRbzyKqfHKf0" 
CURRENT_APP_VERSION = "3.5 PRO"

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/get_version', methods=['GET'])
def get_version(): 
    return jsonify({"version": CURRENT_APP_VERSION})

@app.route('/search', methods=['POST'])
# Cache bypass logic added via frontend timestamp
def search():
    try:
        data = request.get_json()
        q_text = data.get('interest', 'latest jobs').lower()
        
        # --- SMART AGGREGATOR LOGIC ---
        
        # 1. Agar user RESULTS dekh raha hai (Board, SSC, Police)
        if "result" in q_text:
            smart_query = f"{q_text} last 1 year declaration date site:sarkariresult.com OR site:indiaresults.com OR site:fastjobsearchers.com 2025-2026"
        
        # 2. Agar specifically GOVERNMENT JOBS/NOTIFICATIONS hai
        elif any(x in q_text for x in ["govt", "sarkari", "notification", "form live"]):
            smart_query = f"{q_text} official notification last date to apply total post vacancy site:sarkariresult.com OR site:freejobalert.com 2026"
        
        # 3. Agar PRIVATE JOBS/WFH/INTERNSHALA hai
        else:
            # Isme Internshala aur Apna app ko priority di hai
            smart_query = (
                f"{q_text} (site:internshala.com OR site:apna.co OR site:naukri.com OR site:linkedin.com/jobs) "
                f"immediate hiring work from home remote jobs 2026"
            )
        
        headers = {
            'X-API-KEY': SERPER_API_KEY, 
            'Content-Type': 'application/json'
        }
        
        # 50 results taaki filter karne ke liye kaafi data ho
        response = requests.post(
            'https://google.serper.dev/search', 
            headers=headers, 
            json={'q': smart_query, 'num': 50, 'gl': 'in'}, 
            timeout=20
        )
        
        results = response.json().get('organic', [])

        # Post-Processing: Card mein extra details dikhane ke liye snippet clean-up
        processed_results = []
        for item in results:
            # Agar form live hai toh title mein detect karega
            is_live = "apply" in item.get('snippet', '').lower() or "live" in item.get('snippet', '').lower()
            
            processed_results.append({
                "title": item.get('title'),
                "link": item.get('link'),
                "snippet": item.get('snippet'),
                "source": item.get('link').split('/')[2], # Website ka naam (e.g. internshala.com)
                "is_live": is_live
            })

        return jsonify(processed_results)
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
        You are Rozgar AI by R YADAV PRODUCTION. 
        User Name: {name}. Message: {message}.
        Task: Provide specific career advice for Indian students (Bihar/Arwal focus).
        If they ask about govt exams, give info about dates and patterns.
        If they ask about private, suggest Internshala/LinkedIn tips.
        Language: Hinglish.
        """
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload), timeout=30)
        res_json = res.json()
        
        if 'candidates' in res_json:
            reply = res_json['candidates'][0]['content']['parts'][0]['text']
            return jsonify({"reply": reply})
        else:
            return jsonify({"reply": "Bhai, AI server thoda busy hai, dobara try karo."})
            
    except Exception as e:
        return jsonify({"reply": "Network issue! Kripya internet check karein."})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
