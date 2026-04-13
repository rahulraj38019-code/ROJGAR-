import requests
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# API Key configuration
K1 = "268aa2e751d03f3d"
K2 = "61ffa0fe6b46cd80bf6ec73d"
SERPER_API_KEY = K1 + K2

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(os.getcwd(), 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory(os.getcwd(), 'sw.js')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch_jobs', methods=['POST'])
def fetch_jobs():
    try:
        data = request.get_json()
        category = data.get('category', 'latest jobs')
        state = data.get('state', 'India')
        edu = data.get('edu', '')
        page = data.get('page', 1)
        
        # Optimized Logic for Search
        if "Bihar Board" in category:
            query = f"{category} official result 2026 site:biharboardonline.bihar.gov.in OR site:sarkariresult.com"
        elif "SSC" in category:
            query = f"{category} result 2026 merit list site:ssc.gov.in"
        elif "Railway" in category:
            query = f"RRB {category} result 2026 official notice"
        elif "Police" in category:
            query = f"Bihar Police constable result 2026 site:csbc.bih.nic.in"
        elif category == "govt":
            query = f"latest govt jobs for {edu} pass in {state} 2026"
        else:
            query = f"{category} job updates 2026 {state}"

        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        payload = {'q': query, 'num': 10, 'start': (page - 1) * 10, 'gl': 'in'}

        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        results = response.json().get('organic', [])

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
