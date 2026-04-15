import requests
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# --- DIRECT API KEY YAHAN PASTE KARO ---
SERPER_API_KEY = "675ec80f6858652b8add27fbe3ab09371a6faaae"


# AI Key (Bhai yahan apni asli OpenAI key daal dena, warna error aayega)
OPENAI_API_KEY = "yahan_apni_key_daalo" 

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(os.getcwd(), 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory(os.getcwd(), 'sw.js')

@app.route('/')
def index():
    return render_template('index.html')

# --- NAYA LIVE UPDATES ROUTE ---
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
def fetch_jobs():
    try:
        data = request.get_json()
        category = data.get('category', 'latest jobs')
        state = data.get('state', 'India')
        edu = data.get('edu', '')
        page = data.get('page', 1)
        
        # Original logic (kuch bhi delete nahi kiya)
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
        payload = {'q': query, 'num': 40, 'start': (page - 1) * 10, 'gl': 'in'}

        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        results = response.json().get('organic', [])

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)})

# 🔥 NEW AI ROUTE (Fixed: Ab ye crash nahi karega)
@app.route('/ask_ai', methods=['POST'])
def ask_ai():
    try:
        data = request.get_json()
        question = data.get('question')

        # Fix: URL aur Headers ko check kiya
        response = requests.post(
            "https://api.openai.com/v1/chat/completions", # URL thik ki (standard completions)
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini", # Model name standard rakha
                "messages": [{"role": "user", "content": question}]
            }
        )

        result = response.json()
        if 'choices' in result:
            answer = result['choices'][0]['message']['content']
        else:
            answer = "Bhai, AI API key check karo ya recharge khatam ho gaya shayad."
            
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"answer": "Error aa gaya bhai backend mein."})

if __name__ == '__main__':
    app.run(debug=True)
