import requests
from flask import Flask, render_template, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import os
import time
from bs4 import BeautifulSoup
from fpdf import FPDF 
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# --- API KEYS & CONFIG ---
SERPER_API_KEY = "675ec80f6858652b8add27fbe3ab09371a6faaae"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# -----------------
# CACHE & MEMORY
# -----------------
cache = {}
cache_time = {}
CACHE_TTL = 300
chat_memory = {} # V9 Memory Storage
CHAT_STORE = {} # New V9 Pro Storage

# Community Chat Data
chat_messages = [
    {"user": "Sonu_Kumar", "msg": "Bhai Railway Group D ka form kab tak aayega?", "time": "10:45 AM"},
    {"user": "Admin_Rahul", "msg": "November tak umeed hai, taiyari jaari rakhein!", "time": "10:48 AM"}
]

# MODEL LIST (AUTO FALLBACK)
MODELS = [
    "openai/gpt-4o-mini",
    "openai/gpt-3.5-turbo",
    "google/gemini-2.0-flash-lite-preview-02-05:free",
    "mistralai/mistral-small"
]

# V9 PRO SYSTEM PROMPT
SYSTEM_PROMPT = """
You are Rozgar Hub AI Pro (V9 GOD MODE).
Behave like ChatGPT. Be smart, professional, helpful, human-like.
Reply smartly in Hinglish/Hindi/English naturally.
Remember previous messages.
Rules:
- Jobs/result query me details do: post name, eligibility, date, salary, apply process.
- For jobs/results give: Full details, Eligibility, Age, Last date, Apply mode, Selection process.
- If user asks chart/image: reply with text layout.
- Agar info unknown ho to honestly bolo.
"""

# --- BASIC ROUTES ---
@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(os.getcwd(), 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory(os.getcwd(), 'sw.js')

@app.route('/')
def index():
    return render_template('index.html')

# --- LIVE UPDATES (RESULT SECTION) ---
@app.route('/get_live_updates')
def get_live_updates():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
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
    except Exception as e:
        return jsonify({"jobs": [], "admits": []})

# --- JOB SEARCH SECTION ---
@app.route('/fetch_jobs', methods=['POST'])
def fetch_jobs():
    try:
        data = request.get_json()
        category = data.get('category', 'latest jobs')
        edu = data.get('edu', '')
        
        if "Railway" in category or "RRB" in category:
            query = f"RRB Railway {category} official result notice 2026 site:indianrailways.gov.in OR site:sarkariresult.com"
        elif "Bihar Board" in category:
            query = f"BSEB {category} official result 2026 site:biharboardonline.bihar.gov.in OR site:sarkariresult.com"
        elif "SSC" in category:
            query = f"SSC {category} merit list result site:ssc.gov.in OR site:sarkariresult.com"
        elif "Police" in category:
            query = f"Bihar Police {category} result update site:csbc.bih.nic.in OR site:sarkariresult.com"
        else:
            query = f"latest {category} vacancies for {edu} pass 2026 India"

        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        payload = {'q': query, 'num': 20, 'gl': 'in'}
        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        search_data = response.json()
        return jsonify(search_data.get('organic', []))
    except Exception as e:
        return jsonify({"error": str(e)})

# --- RESUME GENERATOR ---
@app.route('/generate_resume', methods=['POST'])
def generate_resume():
    try:
        data = request.form
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="V8 ULTRA RESUME", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Name: {data.get('name', 'N/A')}", ln=True)
        pdf.cell(200, 10, txt=f"Education: {data.get('edu', 'N/A')}", ln=True)
        pdf.multi_cell(0, 10, txt=f"Skills: {data.get('skills', 'N/A')}")
        pdf.multi_cell(0, 10, txt=f"Experience: {data.get('exp', 'N/A')}")
        
        output = io.BytesIO()
        pdf_content = pdf.output(dest='S').encode('latin-1')
        output.write(pdf_content)
        output.seek(0)
        response = make_response(output.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=resume.pdf'
        return response
    except Exception as e:
        return str(e)

# --- CHAT SYSTEM ---
@app.route('/get_messages')
def get_messages():
    return jsonify(chat_messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    new_msg = {"user": data.get('user', 'Guest'), "msg": data.get('msg', ''), "time": "Now"}
    chat_messages.append(new_msg)
    return jsonify({"status": "sent"})


# ===============================
# V9 GOD MODE AI ENGINE (FINAL MERGED)
# ===============================

def ask_model(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    for model in MODELS:
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.7
            }
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=20
            )
            if r.status_code == 200:
                data = r.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            continue
    return None

@app.route("/ask_ai", methods=["POST"])
def ask_ai():
    try:
        data = request.get_json()
        user_msg = (data.get("message") or data.get("question") or "").strip()
        chat_id = data.get("chat_id") or data.get("user_id") or "default"

        if not user_msg:
            return jsonify({"reply": "Question bhejo bhai."})

        if chat_id not in CHAT_STORE:
            CHAT_STORE[chat_id] = []

        history = CHAT_STORE[chat_id]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add last 10 messages for context
        for item in history[-10:]:
            messages.append(item)
            
        messages.append({"role": "user", "content": user_msg})

        reply = ask_model(messages)

        if not reply:
            reply = "⚠️ Sab AI model busy hain. Thodi der baad try karo."

        # Save to Memory
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": reply})
        CHAT_STORE[chat_id] = history

        return jsonify({
            "reply": reply,
            "answer": reply, # compatibility
            "chat_id": chat_id
        })
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

@app.route("/get_chats")
def get_chats():
    result = []
    for cid, msgs in CHAT_STORE.items():
        title = "New Chat"
        for m in msgs:
            if m["role"] == "user":
                title = m["content"][:30]
                break
        result.append({"id": cid, "title": title})
    return jsonify(result)

@app.route("/get_chat/<chat_id>")
def get_chat(chat_id):
    return jsonify(CHAT_STORE.get(chat_id, []))

@app.route("/delete_chat/<chat_id>", methods=["POST"])
def delete_chat(chat_id):
    if chat_id in CHAT_STORE:
        del CHAT_STORE[chat_id]
    return jsonify({"status": "deleted"})

@app.route("/clear_chat", methods=["POST"])
def clear_chat():
    data = request.get_json()
    chat_id = data.get("chat_id")
    if chat_id in CHAT_STORE:
        del CHAT_STORE[chat_id]
    return jsonify({"status": "cleared"})

@app.route("/generate_image", methods=["POST"])
def generate_image():
    data = request.get_json()
    prompt = data.get("prompt", "")
    return jsonify({
        "reply": f"🖼️ Image Prompt Ready: {prompt}",
        "image_url": "https://dummyimage.com/600x400/000/fff&text=AI+IMAGE"
    })

@app.route("/voice_ai", methods=["POST"])
def voice_ai():
    return jsonify({
        "reply": "🎤 Voice feature frontend se connect karo."
    })

# ================= RUN =================
if __name__ == '__main__':
    app.run(debug=True)
