import requests
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# --- TERI NAYI API KEY ---
SERPER_API_KEY = "675ec80f6858652b8add27fbe3ab09371a6faaae"
OPENAI_API_KEY = "yahan_apni_openai_key_daalo" # Agar AI use karna ho toh

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(os.getcwd(), 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory(os.getcwd(), 'sw.js')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_live_updates')
def get_live_updates():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get('https://sarkariresult.com.cm/', headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        jobs, admits = [], []
        all_links = soup.find_all('a')
        for link in all_links:
            text = link.text.strip()
            href = link.get('href', '')
            if not href or len(text) < 10: continue
            if "job" in href.lower() or "recruit" in href.lower():
                if len(jobs) < 15: jobs.append({"title": text, "link": href})
            elif "admit" in href.lower() or "hall-ticket" in href.lower():
                if len(admits) < 15: admits.append({"title": text, "link": href})
        return jsonify({"jobs": jobs, "admits": admits})
    except:
        return jsonify({"jobs": [], "admits": []})

@app.route('/fetch_jobs', methods=['POST'])
def fetch_jobs():
    try:
        data = request.get_json()
        category = data.get('category', 'latest jobs')
        edu = data.get('edu', '')
        
        # Search Queries Logic (Fixed)
        if "Bihar Board" in category:
            query = f"{category} official result 2026 site:biharboardonline.bihar.gov.in OR site:sarkariresult.com"
        elif "SSC" in category:
            query = f"{category} result merit list site:ssc.gov.in OR site:sarkariresult.com"
        elif "Railway" in category:
            query = f"RRB {category} official result notice site:indianrailways.gov.in OR site:sarkariresult.com"
        elif "Police" in category:
            query = f"{category} result updates site:csbc.bih.nic.in OR site:sarkariresult.com"
        else:
            query = f"latest {category} vacancies for {edu} pass 2026 India"

        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        payload = {'q': query, 'num': 20, 'gl': 'in'}

        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        search_data = response.json()
        
        # Check agar Serper error de raha ho
        if "organic" in search_data:
            return jsonify(search_data['organic'])
        else:
            return jsonify({"error": "No results from API"})
            
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/ask_ai', methods=['POST'])
def ask_ai():
    try:
        data = request.get_json()
        question = data.get('question')
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": question}]}
        )
        result = response.json()
        answer = result['choices'][0]['message']['content'] if 'choices' in result else "AI Key Error."
        return jsonify({"answer": answer})
    except:
        return jsonify({"answer": "Error in AI route."})

if __name__ == '__main__':
    app.run(debug=True)
