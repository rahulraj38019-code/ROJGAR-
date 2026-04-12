import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Apni Serper API Key yahan dalo
SERPER_API_KEY = "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch_jobs', methods=['POST'])
def fetch_jobs():
    try:
        data = request.get_json()
        name = data.get('name')
        state = data.get('state')
        edu = data.get('edu')
        
        # Google Search Query: User ki details ke hisaab se
        query = f"latest jobs for {edu} pass in {state} 2026 site:sarkariresult.com OR site:internshala.com OR site:naukri.com"
        
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            'https://google.serper.dev/search',
            headers=headers,
            json={'q': query, 'num': 20, 'gl': 'in'},
            timeout=15
        )
        
        results = response.json().get('organic', [])
        processed = []
        
        for item in results:
            processed.append({
                "title": item.get('title'),
                "link": item.get('link'),
                "snippet": item.get('snippet'),
                "source": "Verified Source"
            })
            
        return jsonify(processed)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=8080)
