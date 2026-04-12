import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Serper API Key
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
        page = data.get('page', 1)

        # --- REFINED SEARCH LOGIC ---
        if category == "govt":
            query = f"latest government jobs for {edu} pass in {state} 2026 site:sarkariresult.com"
        elif category == "wfh":
            query = f"work from home remote jobs India 2026 for {edu} site:naukri.com"
        elif category == "iti":
            query = f"latest ITI apprentice and technician jobs 2026 {state}"
        elif category == "railway":
            query = "RRB Railway recruitment 2026 Group D NTPC ALP official"
        elif category == "bpsc":
            query = "BPSC Bihar Public Service Commission latest updates 2026"
        
        # Specific Result Logic (Tiles ke liye)
        elif "Result" in category:
            query = f"latest {category} 2026 {state} official link check online"
        
        else:
            # Fallback (Agar search bar use karein)
            query = f"{category} latest updates 2026 {state}"

        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
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
