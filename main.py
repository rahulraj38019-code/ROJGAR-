import requests
import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Keys ab Render ke Environment Variables se aayengi
SERPER_API_KEY = os.environ.get("SERPER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@app.route('/')
def index():
    return render_template('index.html')

# --- AI CHAT FEATURE (Groq) ---
@app.route('/ai_chat', methods=['POST'])
def ai_chat():
    try:
        data = request.get_json()
        user_msg = data.get('message', '')
        user_info = data.get('user_info', {})

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        system_prompt = f"Tum ek Career Expert AI ho. User ka naam {user_info.get('name')} hai, jo {user_info.get('state')} se hai aur {user_info.get('edu')} pass hai. Hinglish mein dosti se jawab do."

        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ]
        }

        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        return jsonify({"reply": response.json()['choices'][0]['message']['content']})
    except Exception as e:
        print(f"AI Error: {e}")
        return jsonify({"reply": "Bhai, AI abhi thoda busy hai, thoda ruko!"})

# --- TUMHARE PURANE SAARE FEATURES (Jobs & Results) ---
@app.route('/fetch_jobs', methods=['POST'])
def fetch_jobs():
    try:
        data = request.get_json()
        category = data.get('category', 'latest jobs')
        state = data.get('state', 'India')
        edu = data.get('edu', '')
        page = data.get('page', 1)

        # 1. SSC Result Fix (Wahi purana original logic)
        if category == "SSC Result":
            query = f"SSC GD CGL CHSL MTS official result 2026 site:ssc.gov.in OR site:sarkariresult.com"
        
        # 2. Board Result Fix
        elif category == "Board Result":
            query = f"{state} board 10th 12th exam results 2026 official link"
        
        # 3. Government Jobs for specific education
        elif category == "govt":
            query = f"latest government jobs for {edu} pass in {state} 2026 site:sarkariresult.com"
        
        # 4. Railway Jobs
        elif category == "railway":
            query = "Railway RRB Group D NTPC recruitment 2026 official notification"
        
        # 5. Default Search
        else:
            query = f"{category} latest updates 2026 {state}"

        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        payload = {'q': query, 'num': 10, 'start': (page - 1) * 10, 'gl': 'in'}
        
        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        return jsonify(response.json().get('organic', []))
    except Exception as e:
        print(f"Fetch Error: {e}")
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)
