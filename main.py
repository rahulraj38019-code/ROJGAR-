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
        dob = data.get('dob', '') # DOB handle karne ke liye naya field
        search_query = data.get('search_query', '')
        page = data.get('page', 1)

        # --- SMART QUERY LOGIC (Purana wala delete nahi kiya, bas upgrade kiya hai) ---
        
        if search_query:
            # Agar user result menu se search kare
            query = f"{search_query} official link 2026"
            
        elif category == "govt":
            query = f"latest government jobs for {edu} in {state} 2026 site:sarkariresult.com OR site:freejobalert.com"
            
        elif category == "wfh":
            query = f"work from home remote jobs India 2026 site:linkedin.com OR site:naukri.com"
            
        elif category == "iti":
            query = f"latest ITI apprentice and technician jobs 2026 {state} for {edu} pass"
            
        elif category == "railway":
            query = "Railway RRB recruitment 2026 Group D NTPC ALP Technician official notification"
            
        elif category == "bpsc":
            query = "BPSC Bihar Public Service Commission latest recruitment and exam calendar 2026"

        # --- STATE POLICE & SPECIFIC RESULT LOGIC ---
        elif "Police Result" in category:
            query = f"{category} 2026 {state} merit list official site"
            
        elif "Board Result" in category:
            query = f"10th 12th board exam results 2026 {state} official link"

        elif category == "result":
            # Dashboard ke 'All Result' section ke liye general query
            query = f"latest ssc railway state police results 2026 {state} site:sarkariresult.com"

        else:
            # Default fallback agar kuch match na ho
            query = f"latest jobs and recruitment for {edu} pass in {state} 2026"

        # Age-based filter (optional logic agar query mein DOB use karna ho)
        # Example: if dob: query += f" for age limit check"

        headers = {
            'X-API-KEY': SERPER_API_KEY, 
            'Content-Type': 'application/json'
        }
        
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
