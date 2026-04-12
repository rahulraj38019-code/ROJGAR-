import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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

        # --- REFINED SEARCH LOGIC (SSC & BOARD SEPARATED) ---
        if category == "SSC Result":
            # Specifically targeting Staff Selection Commission
            query = f"SSC GD CGL CHSL MTS official result 2026 site:ssc.gov.in OR site:sarkariresult.com"
        elif category == "Board Result":
            query = f"{state} board 10th 12th exam results 2026 official link"
        elif category == "govt":
            query = f"latest government jobs for {edu} pass in {state} 2026 site:sarkariresult.com"
        elif category == "railway":
            query = "Railway RRB Group D NTPC recruitment 2026 official notification"
        elif "Result" in category:
            query = f"latest {category} 2026 {state} official link"
        else:
            query = f"{category} latest jobs updates 2026 {state}"

        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        payload = {'q': query, 'num': 10, 'start': (page - 1) * 10, 'gl': 'in'}

        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        return jsonify(response.json().get('organic', []))
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
