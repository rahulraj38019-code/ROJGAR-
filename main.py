from utils import send_job_notification 
import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS 
from flask_caching import Cache 
from groq import Groq  # Naya library add kiya
import os, json

app = Flask(__name__)
CORS(app)

# Cache Setup: Performance boost ke liye
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 600})

# API Keys
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d")
# Groq Key yahan set kar di hai
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "Gsk_uNJDRV5iXNlNES4gf5emWGdyb3FY4xskeHog0gwVSOrkrsLVAMlZ")
client = Groq(api_key=GROQ_API_KEY)

CURRENT_APP_VERSION = "3.5 PRO"

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/get_version', methods=['GET'])
def get_version(): 
    return jsonify({"version": CURRENT_APP_VERSION})

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        q_text = data.get('interest', 'latest jobs').lower()
        
        # --- SMART AGGREGATOR LOGIC ---
        if "result" in q_text:
            smart_query = f"{q_text} 2025 2026 site:sarkariresult.com OR site:indiaresults.com"
        elif any(x in q_text for x in ["govt", "sarkari", "police", "ssc", "railway"]):
            smart_query = f"{q_text} notification vacancy 2026 site:freejobalert.com OR site:sarkariresult.com"
        else:
            smart_query = f"{q_text} job vacancy 2026 site:internshala.com OR site:apna.co OR site:naukri.com"

        headers = {
            'X-API-KEY': SERPER_API_KEY, 
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            'https://google.serper.dev/search', 
            headers=headers, 
            json={'q': smart_query, 'num': 40, 'gl': 'in'}, 
            timeout=20
        )
        
        results = response.json().get('organic', [])

        if not results or len(results) < 5:
            backup_res = requests.post(
                'https://google.serper.dev/search', 
                headers=headers, 
                json={'q': f"{q_text} latest updates 2026", 'num': 20}, 
                timeout=15
            )
            results.extend(backup_res.json().get('organic', []))

        processed_results = []
        for item in results:
            link = item.get('link', '')
            source_name = "Official Update"
            
            if "internshala" in link: source_name = "Internshala"
            elif "apna.co" in link: source_name = "Apna App"
            elif "naukri" in link: source_name = "Naukri.com"
            elif "sarkariresult" in link: source_name = "Sarkari Result"
            elif "ssc.nic" in link: source_name = "SSC Official"

            processed_results.append({
                "title": item.get('title'),
                "link": link,
                "snippet": item.get('snippet'),
                "source": source_name,
                "is_live": "apply" in item.get('snippet', '').lower() or "live" in item.get('snippet', '').lower()
            })

        return jsonify(processed_results)
    except Exception as e:
        print(f"Aggregator Error: {e}")
        return jsonify([])

# --- UPDATED CHAT ROUTE (Now using Groq Llama 3) ---
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        name = data.get('name', 'Dost')
        message = data.get('message', '')
        
        # Groq API Call
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"You are Rozgar AI by R YADAV PRODUCTION. User: {name}. Provide career advice in Hinglish. Be friendly and professional."
                },
                {
                    "role": "user",
                    "content": message,
                }
            ],
            model="llama3-8b-8192", # Super fast model
            temperature=0.7,
            max_tokens=1024,
        )

        reply = chat_completion.choices[0].message.content
        return jsonify({"reply": reply})
            
    except Exception as e:
        print(f"Chat Error: {e}")
        return jsonify({"reply": "Network issue! Groq API check karein."})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
