from utils import send_job_notification 
import requests
from flask import Flask, render_template, request, jsonify
import os, json

app = Flask(__name__)

# API Keys
SERPER_API_KEY = "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d"
GEMINI_API_KEY = "AIzaSyDxIVi8NxFf5QEGoXb2wT1FRbzyKqfHKf0" 
CURRENT_APP_VERSION = "2.8" # Version upgrade kar diya

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
        
        # AGGREGATOR LOGIC: Ab ye query LinkedIn, Naukri, aur Indeed ko target karegi
        # Isse user ko 10 alag apps ki zaroorat nahi padegi
        smart_query = f"{q_text} (site:naukri.com OR site:linkedin.com OR site:indeed.com OR site:freshersworld.com) 2026"
        
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        # Results ki sankhya badha kar 50 kar di taaki zyada platforms dikhein
        response = requests.post('https://google.serper.dev/search', headers=headers, json={'q': smart_query, 'num': 50})
        
        return jsonify(response.json().get('organic', []))
    except Exception as e:
        print(f"Search Error: {e}")
        return jsonify([])

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        name = data.get('name', 'User')
        message = data.get('message', '')
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        # AI ko instruct kiya hai ki wo Career Counselor ki tarah reply kare
        prompt = f"""
        You are Rozgar AI by R YADAV PRODUCTION. 
        User Name: {name}
        User Message: {message}
        Task: Help the user with job advice, career paths, or exam info in a friendly way. 
        Use Hinglish (Mix of Hindi and English) as it's for Bihar/India students.
        """
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        # Request timeout 30 rakha hai taaki Render par network error na aaye
        res = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload), timeout=30)
        res_json = res.json()
        
        if 'candidates' in res_json:
            reply = res_json['candidates'][0]['content']['parts'][0]['text']
            return jsonify({"reply": reply})
        else:
            # Agar API limit hit ho jaye toh ye message dikhega
            return jsonify({"reply": "Bhai, AI thoda busy hai, 1 minute baad phir se poocho!"})
            
    except Exception as e:
        print(f"Chat Error: {e}")
        return jsonify({"reply": "Network error! Render server restart ho raha hai ya internet slow hai. Phir se try karein."})

if __name__ == '__main__':
    # Port optimization for Render
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)