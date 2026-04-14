import requests
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from bs4 import BeautifulSoup
import google.generativeai as genai  # 🔥 Nayi Library import ki hai

app = Flask(__name__)
CORS(app)

# API Key configuration
K1 = "268aa2e751d03f3d"
K2 = "61ffa0fe6b46cd80bf6ec73d"
SERPER_API_KEY = K1 + K2

# 🔥 GEMINI API CONFIG (Library setup)
GEMINI_API_KEY = "AIzaSyBf_YPYwWRmcMvquhlAP4-inZy3yOVwAnA"
genai.configure(api_key=GEMINI_API_KEY)

# Model configuration
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(os.getcwd(), 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory(os.getcwd(), 'sw.js')

@app.route('/')
def index():
    return render_template('index.html')

# --- LIVE UPDATES ROUTE (No changes here) ---
@app.route('/get_live_updates')
def get_live_updates():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get('https://sarkariresult.com.cm/', headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        jobs = []
        admits = []
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
    except Exception as e:
        return jsonify({"jobs": [], "admits": []})

@app.route('/fetch_jobs', methods=['POST'])
def fetchData():
    try:
        data = request.get_json()
        category = data.get('category', 'latest jobs')
        state = data.get('state', 'India')
        edu = data.get('edu', '')
        page = data.get('page', 1)
        
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

# 🔥 GEMINI WORKING AI AGENT (Library Method)
@app.route('/ask_ai', methods=['POST'])
def ask_ai():
    try:
        data = request.get_json()
        prompt = data.get('prompt') 

        # Personalized System Instruction taaki AI doston ki tarah baat kare
        system_instruction = (
            "Tum Gemini ho, Rozgar Hub ke users ke liye ek friendly aur witty AI assistant. "
            "Tumhe desi Hinglish mein jawab dena hai. Zyada formalities mat karo, ek dum desi dost banke guide karo."
        )

        # Library se content generate karna
        response = model.generate_content(f"{system_instruction}\n\nUser: {prompt}")
        
        if response.text:
            answer = response.text
        else:
            answer = "Bhai, Google ne response nahi diya. Ek baar phir se pucho!"

        return jsonify({"answer": answer})

    except Exception as e:
        print(f"FATAL_ERROR: {e}")
        return jsonify({"answer": f"Oteri! Ek naya error aa gaya: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)
