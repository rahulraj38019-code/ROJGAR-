import requests
from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

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
        page = data.get('page', 1)
        
        # FIX: Social media sites ko block karne ke liye filter
        exclude_sites = "-site:facebook.com -site:instagram.com -site:twitter.com -site:linkedin.com -site:youtube.com"
        
        if job_type == 'central':
            query = f"central government {interest} vacancy India 2026 {exclude_sites}"
        elif job_type == 'state':
            query = f"{state} government {interest} vacancy 2026 {exclude_sites}"
        else:
            query = f"{interest} latest sarkari vacancy {state} 2026 {exclude_sites}"
            
        headers = {'X-API-KEY': API_KEY, 'Content-Type': 'application/json'}
        payload = {'q': query, 'num': 10, 'page': page}
        
        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        return jsonify(response.json().get('organic', []))
    except Exception as e:
        return jsonify([])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)