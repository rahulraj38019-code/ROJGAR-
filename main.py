import requests
from flask import Flask, render_template, request, jsonify
import os
import json

app = Flask(__name__)

# API Keys
SERPER_API_KEY = "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d"
GEMINI_API_KEY = "AIzaSyC7BwdOrEM38fRsrR3rZzejwbBh7UpOinE"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        interest = data.get('interest', 'latest jobs')
        state = data.get('state', 'India')
        job_type = data.get('type', 'all')
        
        exclude = "-site:facebook.com -site:instagram.com -site:twitter.com -site:youtube.com -site:shiksha.com -site:testbook.com"
        official_filter = "(site:.gov.in OR site:.nic.in OR site:.edu OR site:.res.in OR site:org.in)"

        if job_type == 'results':
            query = f"{interest} exam result 2024 2025 2026 {official_filter} {exclude}"
        elif job_type == 'central':
            query = f"central government {interest} vacancy official notification 2026 {official_filter} {exclude}"
        else:
            query = f"{interest} latest vacancy {state} 2026 {official_filter} {exclude}"
            
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        payload = {'q': query, 'num': 10}
        
        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        return jsonify(response.json().get('organic', []))
    except:
        return jsonify([])

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_msg = data.get('message', '')
        u_name = data.get('name', 'Bhai')
        
        # Gemini API URL
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        # Proper JSON payload for Gemini
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"You are Rozgar AI, a helpful elder brother to {u_name}. Answer career and job questions accurately in a mix of Hindi and English. Be friendly. Question: {user_msg}"
                }]
            }]
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            result = response.json()
            ai_reply = result['candidates'][0]['content']['parts'][0]['text']
            return jsonify({"reply": ai_reply})
        else:
            # Render error logs ke liye
            print(f"Gemini Error: {response.text}")
            return jsonify({"reply": "Bhai, API side se dikkat hai. Key check karo ya thoda wait karo."})
            
    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({"reply": "Bhai, server thoda busy hai. Ek baar refresh karke try karo!"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)