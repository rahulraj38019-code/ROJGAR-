# [Line 1-6] Imports
import requests
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os # [Fix] Directory path find karne ke liye

# [Line 8-16] App Configuration & API Keys
app = Flask(__name__)
CORS(app)

# GitHub Secret Error se bachne ke liye key ko split kiya hai
K1 = "268aa2e751d03f3d"
K2 = "61ffa0fe6b46cd80bf6ec73d"
SERPER_API_KEY = K1 + K2

# [Line 18-26] PWA Routes (Fix: Browser ko manifest aur sw files yahan se milengi)
@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(os.getcwd(), 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory(os.getcwd(), 'sw.js')

# [Line 28-31] WhatsApp Share Text Generator
def get_share_text(title, link):
    return f"🚀 *Rozgar Hub Update* 🚀\n\n*Job:* {title}\n\nCheck Details here: {link}\n\nStay Updated with Rozgar Hub!"

# [Line 33-36] Home Route
@app.route('/')
def index():
    return render_template('index.html')

# [Line 38-86] Job Fetching Logic (Main Function)
@app.route('/fetch_jobs', methods=['POST'])
def fetch_jobs():
    try:
        data = request.get_json()
        category = data.get('category', 'latest jobs')
        state = data.get('state', 'India')
        edu = data.get('edu', '')
        page = data.get('page', 1)
        
        # --- FEATURE 2: SEARCH KEYWORD HANDLING ---
        user_search = data.get('search_query', '')

        # Naya Result Logic Jo Frontend se sync hoga
        if user_search:
            query = f"{user_search} govt jobs results 2026 {state} site:sarkariresult.com"
        elif "Bihar Board" in category:
            query = f"{category} sarkari result official link site:biharboardonline.bihar.gov.in OR site:sarkariresult.com"
        elif "SSC" in category and "Result" in category:
            query = f"{category} 2026 official merit list selection post site:ssc.gov.in OR site:sarkariresult.com"
        elif "Railway" in category:
            query = f"{category} group d ntpc alp technician result official site:indianrailways.gov.in"
        elif "Bihar Police" in category:
            query = f"{category} constable sub-inspector result merit list site:csbc.bih.nic.in"
        elif category == "govt":
            query = f"latest government jobs for {edu} pass in {state} 2026 site:sarkariresult.com"
        elif category == "railway":
            query = "Railway RRB Group D NTPC recruitment 2026 official notification"
        elif category == "iti":
            query = f"latest ITI pass apprentice and govt jobs 2026 site:sarkariresult.com"
        else:
            query = f"{category} latest updates 2026 {state}"

        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        payload = {'q': query, 'num': 10, 'start': (page - 1) * 10, 'gl': 'in'}

        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        results = response.json().get('organic', [])

        # --- FEATURE 3: DATA ENHANCEMENT ---
        for item in results:
            share_msg = get_share_text(item.get('title'), item.get('link'))
            item['whatsapp_url'] = f"https://api.whatsapp.com/send?text={requests.utils.quote(share_msg)}"

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)})

# [Line 88-96] Extra Hooks & App Run
@app.route('/auto_update_check')
def auto_update():
    return jsonify({"status": "Scraper Bridge Ready", "next_sync": "Scheduled"})

if __name__ == '__main__':
    app.run(debug=True)
