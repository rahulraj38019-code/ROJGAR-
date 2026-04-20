import requests
from flask import Flask, render_template, request, jsonify, send_from_directory, make_response, send_file
from flask_cors import CORS
import os
import json
import time
import uuid
from bs4 import BeautifulSoup
from fpdf import FPDF 
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract

app = Flask(__name__)
CORS(app)

# ===============================
# CONFIG & API KEYS
# ===============================
SERPER_API_KEY = "675ec80f6858652b8add27fbe3ab09371a6faaae"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

UPLOAD_FOLDER = "uploads"
CHAT_FOLDER = "saved_chats"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHAT_FOLDER, exist_ok=True)

# -----------------
# CACHE & MEMORY
# -----------------
cache = {}
cache_time = {}
CACHE_TTL = 300
chat_memory = {} 
users_db = {}

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

# ===============================
# HELPERS & UTIL
# ===============================
def get_chat_file(uid):
    return f"{CHAT_FOLDER}/{uid}.json"

def load_user_chat(uid):
    path = get_chat_file(uid)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_user_chat(uid, data):
    with open(get_chat_file(uid), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- NEW FUNCTIONS ---
def get_live_data(query):
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "gl": "in", "hl": "en"}

    r = requests.post(
        "https://google.serper.dev/search",
        headers=headers,
        json=payload,
        timeout=10
    )

    results = r.json().get("organic", [])

    context = ""
    for item in results[:5]:
        context += f"- {item.get('title')} : {item.get('snippet')}\n"

    return context

def ask_ai(messages):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": messages,
        "temperature": 0.7
    }

    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=40
    )

    return r.json()["choices"][0]["message"]["content"]

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

# =========================================================
# LOGIN & LIVE UPDATES
# =========================================================
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username", "").strip()
    if not username:
        return jsonify({"status": "error", "msg": "Username required"})
    users_db[username] = True
    return jsonify({"status": "success", "username": username})

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
@app.route('/jobs', methods=['POST'])
def fetch_jobs():
    try:
        data = request.get_json()
        category = data.get('category', 'latest jobs')
        edu = data.get('edu', '')
        query = data.get('query')

        if query:
            final_query = query
        elif "Railway" in category or "RRB" in category:
            final_query = f"RRB Railway {category} official result notice 2026 site:indianrailways.gov.in OR site:sarkariresult.com"
        elif "Bihar Board" in category:
            final_query = f"BSEB {category} official result 2026 site:biharboardonline.bihar.gov.in OR site:sarkariresult.com"
        elif "SSC" in category:
            final_query = f"SSC {category} merit list result site:ssc.gov.in OR site:sarkariresult.com"
        elif "Police" in category:
            final_query = f"Bihar Police {category} result update site:csbc.bih.nic.in OR site:sarkariresult.com"
        else:
            final_query = f"latest {category} vacancies for {edu} pass 2026 India"

        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        payload = {'q': final_query, 'num': 20, 'gl': 'in'}
        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        search_data = response.json()
        return jsonify(search_data.get('organic', []))
    except Exception as e:
        return jsonify({"error": str(e)})

# ===============================
# LIVE SEARCH (V10)
# ===============================
@app.route("/live_search", methods=["POST"])
def live_search():
    try:
        data = request.json
        q = data.get("query")
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        payload = {"q": q, "gl": "in", "hl": "en"}
        r = requests.post("https://google.serper.dev/search", headers=headers, json=payload)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)})

# --- RESUME GENERATOR ---
@app.route('/generate_resume', methods=['POST'])
@app.route('/resume', methods=['POST'])
def generate_resume():
    try:
        if request.is_json:
            data = request.json
        else:
            data = request.form
            
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="VidyaJobs.AI ULTRA RESUME", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        
        if not request.is_json:
            pdf.cell(200, 10, txt=f"Name: {data.get('name', 'N/A')}", ln=True)
            pdf.cell(200, 10, txt=f"Education: {data.get('edu', 'N/A')}", ln=True)
            pdf.multi_cell(0, 10, txt=f"Skills: {data.get('skills', 'N/A')}")
            pdf.multi_cell(0, 10, txt=f"Experience: {data.get('exp', 'N/A')}")
        else:
            for k, v in data.items():
                pdf.cell(200, 10, f"{k}: {v}", ln=True)

        output = io.BytesIO()
        pdf_content = pdf.output(dest='S').encode('latin-1')
        output.write(pdf_content)
        output.seek(0)
        return send_file(output, download_name="resume.pdf", as_attachment=True)
    except Exception as e:
        return str(e)

# ===============================
# FILE & PDF & OCR HANDLING
# ===============================
@app.route("/upload_file", methods=["POST"])
@app.route("/upload", methods=["POST"])
def upload_file():
    try:
        file = request.files["file"]
        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        return jsonify({"success": True, "filename": filename, "path": path})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/read_pdf", methods=["POST"])
def read_pdf():
    try:
        file = request.files["file"]
        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        reader = PdfReader(path)
        text = "".join([p.extract_text() or "" for p in reader.pages])
        return jsonify({"success": True, "text": text[:15000]})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/ocr", methods=["POST"])
def ocr():
    try:
        file = request.files["file"]
        img = Image.open(file)
        text = pytesseract.image_to_string(img)
        return jsonify({"success": True, "text": text})
    except Exception as e:
        return jsonify({"error": str(e)})

# ===============================
# IMAGE & AI ROUTES
# ===============================
@app.route("/generate_image", methods=["POST"])
@app.route("/image", methods=["POST"])
def generate_image():
    try:
        data = request.json
        prompt = data.get("prompt")
        payload = {"model": "openai/dall-e-3", "prompt": prompt, "n": 1}
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
        r = requests.post("https://openrouter.ai/api/v1/images/generations", headers=headers, json=payload)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)})

# --- UPDATED AI ROUTE ---
@app.route("/ask_ai_v10", methods=["POST"])
def ask_ai_v10():
    try:
        data = request.json
        msg = data.get("message")
        uid = data.get("uid", "guest")

        history = load_user_chat(uid)

        # 🔥 detect if live data needed
        keywords = ["job", "latest", "news", "result", "update", "vacancy"]
        need_live = any(k in msg.lower() for k in keywords)

        live_context = ""
        if need_live:
            live_context = get_live_data(msg)

        system_prompt = f"""
You are VidyaJobs.AI V10 ULTRA AI.

RULES:
- Always use latest info if provided
- If live data exists, prioritize it
- Be accurate and simple
- If unsure, say "latest update may vary"

LIVE DATA:
{live_context}
"""

        messages = [{"role": "system", "content": system_prompt}]
        messages += history[-10:]
        messages.append({"role": "user", "content": msg})

        answer = ask_ai(messages)

        history.append({"role": "user", "content": msg})
        history.append({"role": "assistant", "content": answer})

        save_user_chat(uid, history)

        return jsonify({
            "reply": answer,
            "live_used": bool(live_context)
        })

    except Exception as e:
        return jsonify({
            "reply": "AI system busy hai bhai 😅",
            "error": str(e)
        })

# ===============================
# CHAT MANAGEMENT
# ===============================
@app.route("/save_chat", methods=["POST"])
def save_chat():
    try:
        data = request.json
        uid = data.get("uid")
        chats = data.get("chats")
        save_user_chat(uid, chats)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/load_chat", methods=["POST"])
def load_chat():
    try:
        data = request.json
        uid = data.get("uid")
        chats = load_user_chat(uid)
        return jsonify({"success": True, "chats": chats})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/recent_chats", methods=["GET"])
def recent_chats():
    try:
        files = os.listdir(CHAT_FOLDER)
        users = [x.replace(".json", "") for x in files if x.endswith(".json")]
        return jsonify({"users": users})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/delete_chat", methods=["POST"])
def delete_chat():
    try:
        data = request.json
        uid = data.get("uid")
        path = get_chat_file(uid)
        if os.path.exists(path):
            os.remove(path)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)})

# --- COMMUNITY CHAT SYSTEM ---
@app.route('/get_messages')
@app.route('/chat/get')
def get_messages():
    return jsonify(chat_messages)

@app.route('/send_message', methods=['POST'])
@app.route('/chat/send', methods=['POST'])
def send_message():
    data = request.get_json()
    new_msg = {
        "user": data.get('user', 'Guest'), 
        "msg": data.get('msg', ''), 
        "time": time.strftime("%I:%M %p") if "time" not in data else data.get("time")
    }
    chat_messages.append(new_msg)
    return jsonify({"status": "sent", "ok": True})

# ================= RUN =================
if __name__ == '__main__':
    app.run(debug=True)
