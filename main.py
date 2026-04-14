import requests
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# API Key configuration (Bhai, ye tere purane keys hi hain)
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

# --- 1. SMART RECOMMENDATIONS ROUTE (Naya Feature) ---
# Ye route user ki education aur state ke hisab se automatic jobs dhundhega
@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    try:
        data = request.get_json()
        edu = data.get('edu', 'Graduate')
        state = data.get('state', 'India')
        
        # Smart Query: User ki padhai ke hisab se top 5 jobs
        query = f"latest govt jobs for {edu} pass in {state} 2026 official"
        
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        payload = {'q': query, 'num': 5, 'gl': 'in'}

        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        results = response.json().get('organic', [])
        
        return jsonify(results)
    except Exception as e:
        return jsonify([])

# --- 2. LIVE UPDATES ROUTE (Tera Scraping Logic - Safe Hai) ---
@app.route('/get_live_updates')
def get_live_updates():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        # Hum wahi site scrape kar rahe hain jo tune set ki thi
        response = requests.get('https://sarkariresult.com.cm/', headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        jobs = []
        admits = []
        all_links = soup.find_all('a')
        
        for link in all_links:
            text = link.text.strip()
            href = link.get('href', '')
            if not href or len(text) < 10: continue

            # "Job" aur "Admit Card" filter logic
            if "job" in href.lower() or "recruit" in href.lower():
                if len(jobs) < 15: jobs.append({"title": text, "link": href})
            elif "admit" in href.lower() or "hall-ticket" in href.lower():
                if len(admits) < 15: admits.append({"title": text, "link": href})

        return jsonify({"jobs": jobs, "admits": admits})
    except Exception as e:
        return jsonify({"jobs": [], "admits": []})

# --- 3. MAIN FETCH JOBS ROUTE (Search Logic) ---
@app.route('/fetch_jobs', methods=['POST'])
def fetch_jobs():
    try:
        data = request.get_json()
        category = data.get('category', 'latest jobs')
        state = data.get('state', 'India')
        edu = data.get('edu', '')
        page = data.get('page', 1)
        
        # Pura query logic wahi rakha hai jo tune banaya tha
        if "Bihar Board" in category:
            query = f"{category} official result site:biharboardonline.bihar.gov.in OR site:sarkariresult.com"
        elif "SSC" in category:
            query = f"{category} merit list site:ssc.gov.in OR site:sarkariresult.com"
        elif "Railway" in category:
            query = f"RRB {category} official result notice site:indianrailways.gov.in OR site:sarkariresult.com"
        elif "Police" in category:
            query = f"{category} result official updates site:csbc.bih.nic.in OR site:sarkariresult.com"
        elif category == "govt":
            query = f"latest govt jobs for {edu} pass in {state} 2026"
        else:
            query = f"{category}"

        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        payload = {'q': query, 'num': 10, 'start': (page - 1) * 10, 'gl': 'in'}

        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        results = response.json().get('organic', [])

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    # Isko 0.0.0.0 par rakha hai taaki network par bhi access ho sake
    app.run(host='0.0.0.0', port=5000, debug=True)
