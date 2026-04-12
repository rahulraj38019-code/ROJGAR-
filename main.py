from utils import send_job_notification 
import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # Naya: Connectivity ke liye
from flask_caching import Cache # Naya: Speed ke liye
import os, json

app = Flask(__name__)
CORS(app) # Browser connectivity error fix karta hai

# Cache Setup: Results ko 10 minute tak yaad rakhega taaki app fast chale
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 600})

# API Keys
SERPER_API_KEY = "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d"
GEMINI_API_KEY = "AIzaSyDxIVi8NxFf5QEGoXb2wT1FRbzyKqfHKf0" 
CURRENT_APP_VERSION = "2.9" # Pro Version Update

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/get_version', methods=['GET'])
def get_version(): 
    return jsonify({"version": CURRENT_APP_VERSION})

@app.route('/search', methods=['POST'])
@cache.cached(timeout=600, query_string=True) # Same search par baar-baar API call nahi hogi
def search():
    try:
        data = request.get_json()
        q_text = data.get('interest', 'latest jobs')
        
        # PRO AGGREGATOR: LinkedIn, Naukri, Indeed aur FreshersWorld ko scan karta hai
        smart_query = f"{q_text} (site:naukri.com OR site:linkedin.com OR site:indeed.com OR site:freshersworld.com) 2026"
        
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        response = requests.post('https://google.serper.dev/search', headers=headers, json={'q': smart_query, 'num': 50}, timeout=15)
        
        return jsonify(response.json().get('organic', []))
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
        
        # AI Persona: Ab ye aur bhi friendly aur professional baat karega
        prompt = f"""
        You are Rozgar AI, a professional career assistant by R YADAV PRODUCTION.
        The user's name is {name}. 
        User's question: {message}
        Your goal: Provide helpful, encouraging, and accurate career/job advice in Hinglish.
        Keep it concise, friendly, and motivating for students in Bihar and India.
        """
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        # Timeout 30 rakha hai taaki Render ke slow network par bhi response aaye
        res = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload), timeout=30)
        res_json = res.json()
        
        if 'candidates' in res_json:
            reply = res_json['candidates'][0]['content']['parts'][0]['text']
            return jsonify({"reply": reply})
        else:
            return jsonify({"reply": "Bhai, AI thoda busy hai, kripya 1 minute baad koshish karein!"})
            
    except Exception as e:
        print(f"Chat Error: {e}")
        return jsonify({"reply": "Network Error: Server se connect nahi ho pa rahe. Ek baar internet check karein!"})

if __name__ == '__main__':
    # Render optimization
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)