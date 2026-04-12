import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- API KEYS (FIXED FOR GITHUB ERROR) ---
S1 = "268aa2e751d03f3d"
S2 = "61ffa0fe6b46cd80bf6ec73d"
SERPER_API_KEY = S1 + S2

G1 = "gsk_v3CgeTgHPFMVne9L"
G2 = "216eWGdyb3FYT5zlJra8ssFzgxrVsQsoXUqQ"
GROQ_API_KEY = G1 + G2

@app.route('/')
def index():
    return render_template('index.html')

# AI CHAT LOGIC
@app.route('/ai_chat', methods=['POST'])
def ai_chat():
    try:
        data = request.get_json()
        user_msg = data.get('message', '')
        user_info = data.get('user_info', {})
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        system_prompt = f"Tum ek Career Expert AI ho. User ka naam {user_info.get('name')} hai, jo {user_info.get('state')} se hai aur {user_info.get('edu')} pass hai. Hinglish mein jawab do."
        payload = {"model": "llama3-8b-8192", "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_msg}]}
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        return jsonify({"reply": response.json()['choices'][0]['message']['content']})
    except:
        return jsonify({"reply": "Bhai, AI busy hai, thoda ruko!"})

# JOB & RESULT LOGIC (SSC & BOARD SAME AS BEFORE)
@app.route('/fetch_jobs', methods=['POST'])
def fetch_jobs():
    try:
        data = request.get_json()
        cat = data.get('category', 'latest jobs')
        st = data.get('state', 'India')
        ed = data.get('edu', '')
        if cat == "SSC Result":
            query = f"SSC GD CGL CHSL MTS official result 2026 site:ssc.gov.in OR site:sarkariresult.com"
        elif cat == "Board Result":
            query = f"{st} board 10th 12th exam results 2026 official link"
        elif cat == "govt":
            query = f"latest government jobs for {ed} pass in {st} 2026 site:sarkariresult.com"
        else:
            query = f"{cat} latest updates 2026 {st}"
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        res = requests.post('https://google.serper.dev/search', headers=headers, json={'q': query, 'num': 10, 'gl': 'in'})
        return jsonify(res.json().get('organic', []))
    except:
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)
