import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Apni API KEY yahan check kar lena
SERPER_API_KEY = "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d"

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
        search_query = data.get('search_query', '')
        page = data.get('page', 1)

        # Smart Query Building
        if search_query:
            query = f"{search_query} details and link 2026"
        elif category == "govt":
            query = f"latest government jobs for {edu} in {state} 2026 site:sarkariresult.com OR site:freejobalert.com"
        elif category == "wfh":
            query = f"work from home remote jobs India 2026 site:linkedin.com OR site:naukri.com"
        elif category == "iti":
            query = f"latest ITI apprentice and technician jobs 2026 {state}"
        elif category == "railway":
            query = "Railway RRB recruitment 2026 Group D NTPC ALP official"
        elif category == "result":
            query = f"latest exam results 10th 12th SSC {state} Police 2026"
        elif category == "bpsc":
            query = "BPSC Bihar Public Service Commission latest notification 2026"
        else:
            query = f"latest jobs for {edu} in {state} 2026"

        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        
        # 'start' parameter page wise data lata hai
        payload = {
            'q': query,
            'num': 10,
            'start': (page - 1) * 10,
            'gl': 'in'
        }

        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        return jsonify(response.json().get('organic', []))
    
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
