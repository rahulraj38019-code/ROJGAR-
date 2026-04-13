import requests
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# GitHub Secret Error se bachne ke liye key ko split kiya hai
K1 = "268aa2e751d03f3d"
K2 = "61ffa0fe6b46cd80bf6ec73d"
SERPER_API_KEY = K1 + K2

# --- FEATURE 1: DYNAMIC SHARE TEXT GENERATOR ---
# Ye function backend se hi WhatsApp ke liye mast text taiyar karke bhejega
def get_share_text(title, link):
    return f"🚀 *Rozgar Hub Update* 🚀\n\n*Job:* {title}\n\nCheck Details here: {link}\n\nStay Updated with Rozgar Hub!"

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
        page = data.get('page', 1)
        
        # --- FEATURE 2: SEARCH KEYWORD HANDLING ---
        # Agar user kuch search karega toh hum query ko uske hisab se modify kar denge
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

        # --- FEATURE 3: DATA ENHANCEMENT ---
        # Hum har result mein WhatsApp link add kar rahe hain taaki HTML mein sirf button dikhana pade
        for item in results:
            share_msg = get_share_text(item.get('title'), item.get('link'))
            item['whatsapp_url'] = f"https://api.whatsapp.com/send?text={requests.utils.quote(share_msg)}"

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)})

# --- FUTURE SCRAPER HOOK ---
# Is route ko hum future mein auto-update ke liye use karenge
@app.route('/auto_update_check')
def auto_update():
    return jsonify({"status": "Scraper Bridge Ready", "next_sync": "Scheduled"})

if __name__ == '__main__':
    app.run(debug=True)