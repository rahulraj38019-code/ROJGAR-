from utils import send_job_notification 
import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS 
from flask_caching import Cache 
import os, json

app = Flask(__name__)
CORS(app)

# Cache Setup: Performance boost ke liye
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 600})

# API Keys (Render ke Environment Variables se uthayega)
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDxIVi8NxFf5QEGoXb2wT1FRbzyKqfHKf0") 
CURRENT_APP_VERSION = "3.5 PRO"

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
        q_text = data.get('interest', 'latest jobs').lower()
        
        # --- SMART AGGREGATOR LOGIC (Fix: Ab results miss nahi honge) ---
        if "result" in q_text:
            # Results ke liye best sites target karega
            smart_query = f"{q_text} 2025 2026 site:sarkariresult.com OR site:indiaresults.com"
        elif any(x in q_text for x in ["govt", "sarkari", "police", "ssc", "railway"]):
            # Govt jobs ke liye official notification focus
            smart_query = f"{q_text} notification vacancy 2026 site:freejobalert.com OR site:sarkariresult.com"
        else:
            # Private jobs ke liye Internshala, Apna aur Naukri target
            smart_query = f"{q_text} job vacancy 2026 site:internshala.com OR site:apna.co OR site:naukri.com"

        headers = {
            'X-API-KEY': SERPER_API_KEY, 
            'Content-Type': 'application/json'
        }
        
        # API Call
        response = requests.post(
            'https://google.serper.dev/search', 
            headers=headers, 
            json={'q': smart_query, 'num': 40, 'gl': 'in'}, 
            timeout=20
        )
        
        results = response.json().get('organic', [])

        # BACKUP: Agar results nahi mile toh generic search karega
        if not results or len(results) < 5:
            backup_res = requests.post(
                'https://google.serper.dev/search', 
                headers=headers, 
                json={'q': f"{q_text} latest updates 2026", 'num': 20}, 
                timeout=15
            )
            results.extend(backup_res.json().get('organic', []))

        # Frontend ke liye data format karna
        processed_results = []
        for item in results:
            link = item.get('link', '')
            source_name = "Official Update"
            
            # Platform identify karna link se
            if "internshala" in link: source_name = "Internshala"
            elif "apna.co" in link: source_name = "Apna App"
            elif "naukri" in link: source_name = "Naukri.com"
            elif "sarkariresult" in link: source_name = "Sarkari Result"
            elif "ssc.nic" in link: source_name = "SSC Official"

            processed_results.append({
                "title": item.get('title'),
                "link": link,
                "snippet": item.get('snippet'),
                "source": source_name,
                "is_live": "apply" in item.get('snippet', '').lower() or "live" in item.get('snippet', '').lower()
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
        
        prompt = f"You are Rozgar AI by R YADAV PRODUCTION. User: {name}. Message: {message}. Provide career advice in Hinglish."
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload), timeout=30)
        res_json = res.json()
        
        if 'candidates' in res_json:
            reply = res_json['candidates'][0]['content']['parts'][0]['text']
            return jsonify({"reply": reply})
        else:
            return jsonify({"reply": "AI thoda busy hai, dobara koshish karein!"})
            
    except Exception as e:
        return jsonify({"reply": "Network issue! Check internet."})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
