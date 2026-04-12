import requests
from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

# Serper API Key (Search ke liye)
API_KEY = "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d"

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
        
        exclude_sites = "-site:facebook.com -site:instagram.com -site:twitter.com -site:linkedin.com -site:youtube.com"
        
        # Result button aur filtering ke liye logic
        if job_type == 'results':
            query = f"latest sarkari exam results 2026 {state} {exclude_sites}"
        elif job_type == 'central':
            query = f"central government {interest} vacancy India 2026 {exclude_sites}"
        elif job_type == 'state':
            query = f"{state} government {interest} vacancy 2026 {exclude_sites}"
        else:
            query = f"{interest} latest vacancy {state} 2026 {exclude_sites}"
            
        headers = {'X-API-KEY': API_KEY, 'Content-Type': 'application/json'}
        payload = {'q': query, 'num': 10}
        
        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        return jsonify(response.json().get('organic', []))
    except Exception as e:
        return jsonify([])

# Real AI Chatbot Command Logic
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_msg = data.get('message', '').lower()
        state = data.get('state', 'Bihar')
        
        # Real-time search for chatbot answers
        query = f"{user_msg} information for students in {state} India 2026"
        headers = {'X-API-KEY': API_KEY, 'Content-Type': 'application/json'}
        payload = {'q': query, 'num': 1}
        
        search_res = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        results = search_res.json().get('organic', [])
        
        if results:
            reply = f"Bhai, meri research ke hisab se: {results[0]['snippet']}"
        else:
            reply = "Bhai, is baare mein abhi pakki jaankari nahi mili. Kya main kuch aur search karoon?"
            
        return jsonify({"reply": reply})
    except:
        return jsonify({"reply": "Network error, thodi der baad puchiye!"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)