import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- UPDATE SYSTEM CONFIG ---
APP_VERSION = "1.1" # Jab update dena ho, ise badal dena (e.g. 1.2)

K1 = "268aa2e751d03f3d"
K2 = "61ffa0fe6b46cd80bf6ec73d"
SERPER_API_KEY = K1 + K2

def get_share_text(title, link):
    return f"🚀 *Rozgar Hub Update* 🚀\n\n*Job:* {title}\n\nCheck Details here: {link}\n\nStay Updated with Rozgar Hub!"

@app.route('/')
def index():
    return render_template('index.html')

# Naya route version check ke liye
@app.route('/check_app_update')
def check_app_update():
    return jsonify({"version": APP_VERSION})

@app.route('/fetch_jobs', methods=['POST'])
def fetch_jobs():
    try:
        data = request.get_json()
        category = data.get('category', 'latest jobs')
        state = data.get('state', 'India')
        edu = data.get('edu', '')
        page = data.get('page', 1)
        user_search = data.get('search_query', '')

        if user_search:
            query = f"{user_search} govt jobs results 2026 {state} site:sarkariresult.com"
        elif category == "SSC Result":
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
        results = response.json().get('organic', [])

        for item in results:
            share_msg = get_share_text(item.get('title'), item.get('link'))
            item['whatsapp_url'] = f"https://api.whatsapp.com/send?text={requests.utils.quote(share_msg)}"

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/auto_update_check')
def auto_update():
    return jsonify({"status": "Scraper Bridge Ready", "next_sync": "Scheduled"})

if __name__ == '__main__':
    app.run(debug=True)
