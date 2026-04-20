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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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

# ---------------- LIVE DATA ----------------
def get_live_data(query):
    try:
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
    except:
        return ""

# ---------------- AI CALL ----------------
def ask_ai(messages):
    try:
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
    except:
        return "AI temporarily busy 😅"

# ===============================
# ROUTES
# ===============================
@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(os.getcwd(), 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory(os.getcwd(), 'sw.js')

@app.route('/')
def index():
    return render_template('index.html')

# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username", "").strip()
    if not username:
        return jsonify({"status": "error", "msg": "Username required"})
    users_db[username] = True
    return jsonify({"status": "success", "username": username})

# ---------------- LIVE UPDATES ----------------
@app.route('/get_live_updates')
def get_live_updates():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get('https://sarkariresult.com.cm/', headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        jobs, admits = [], []

        for link in soup.find_all('a'):
            text = link.text.strip()
            href = link.get('href', '')
            if not href or len(text) < 10:
                continue

            if "admit" in href.lower():
                admits.append({"title": text, "link": href})
            else:
                jobs.append({"title": text, "link": href})

        return jsonify({"jobs": jobs[:15], "admits": admits[:15]})

    except:
        return jsonify({"jobs": [], "admits": []})

# ---------------- JOB SEARCH ----------------
@app.route('/fetch_jobs', methods=['POST'])
@app.route('/jobs', methods=['POST'])
def fetch_jobs():
    try:
        data = request.get_json()
        category = data.get('category', 'latest jobs')
        edu = data.get('edu', '')
        query = data.get('query')

        final_query = query or f"latest {category} jobs {edu}"

        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        payload = {'q': final_query, 'num': 20, 'gl': 'in'}

        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        search_data = response.json()

        return jsonify(search_data.get('organic', []))

    except Exception as e:
        return jsonify({"error": str(e)})

# ---------------- LIVE SEARCH ----------------
@app.route("/live_search", methods=["POST"])
def live_search():
    try:
        data = request.json
        q = data.get("query")

        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        payload = {"q": q, "gl": "in", "hl": "en"}

        r = requests.post("https://google.serper.dev/search", headers=headers, json=payload)

        return jsonify(r.json())
    except:
        return jsonify({"error": "failed"})

# ---------------- AI ROUTE ----------------
@app.route("/ask_ai_v10", methods=["POST"])
def ask_ai_v10():
    try:
        data = request.json
        msg = data.get("message")
        uid = data.get("uid", "guest")

        history = load_user_chat(uid)

        keywords = ["job", "latest", "news", "result", "update", "vacancy"]
        live_context = ""

        if any(k in msg.lower() for k in keywords):
            live_context = get_live_data(msg)

        system_prompt = f"""
You are VidyaJobs.AI V10 ULTRA AI.

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

        return jsonify({"reply": answer, "live_used": bool(live_context)})

    except Exception as e:
        return jsonify({"reply": "AI busy 😅", "error": str(e)})

# ---------------- CHAT ----------------
@app.route("/save_chat", methods=["POST"])
def save():
    d = request.json
    save_user_chat(d["uid"], d["chats"])
    return jsonify({"ok": True})

@app.route("/load_chat", methods=["POST"])
def load():
    uid = request.json["uid"]
    return jsonify({"chats": load_user_chat(uid)})

@app.route("/recent_chats")
def recent():
    files = os.listdir(CHAT_FOLDER)
    return jsonify({"users": [f.replace(".json", "") for f in files]})

@app.route("/delete_chat", methods=["POST"])
def delete():
    uid = request.json["uid"]
    path = get_chat_file(uid)
    if os.path.exists(path):
        os.remove(path)
    return jsonify({"ok": True})

# ---------------- COMMUNITY ----------------
@app.route("/get_messages")
def msgs():
    return jsonify(chat_messages)

@app.route("/send_message", methods=["POST"])
def send():
    d = request.json
    chat_messages.append({
        "user": d.get("user", "Guest"),
        "msg": d.get("msg", ""),
        "time": time.strftime("%I:%M %p")
    })
    return jsonify({"ok": True})

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)