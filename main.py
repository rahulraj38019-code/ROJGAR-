import requests
from flask import Flask, render_template, request, jsonify
import os

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
        
        # STRICT FILTER: Third-party sites ko poora block kar diya
        exclude = "-site:facebook.com -site:instagram.com -site:twitter.com -site:youtube.com -site:shiksha.com -site:indiatoday.in -site:jagranjosh.com -site:testbook.com"
        # OFFICIAL ONLY: Sirf govt aur official domains ko force karega
        official_filter = "(site:.gov.in OR site:.nic.in OR site:.edu OR site:.res.in OR site:org.in)"

        if job_type == 'results':
            query = f"{interest} exam result 2024 2025 2026 {official_filter} {exclude}"
        elif job_type == 'central':
            query = f"central government {interest} vacancy official notification 2026 {official_filter} {exclude}"
        else:
            query = f"{state} government {interest} vacancy official portal 2026 {official_filter} {exclude}"
            
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
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        prompt = {
            "contents": [{
                "parts": [{
                    "text": f"You are Rozgar AI, a helpful elder brother to {u_name}. Answer career and job questions accurately in Hindi/English mix. Question: {user_msg}"
                }]
            }]
        }
        
        res = requests.post(url, json=prompt)
        ai_reply = res.json()['candidates'][0]['content']['parts'][0]['text']
        return jsonify({"reply": ai_reply})
    except:
        return jsonify({"reply": "Bhai, network issue hai. Thodi der baad puchho!"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)