import requests
from flask import Flask, render_template, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import os
import time
from bs4 import BeautifulSoup
from fpdf import FPDF # Resume generation ke liye
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
CORS(app)

# ===================== CONFIG & CACHE =====================
SERPER_API_KEY = "675ec80f6858652b8add27fbe3ab09371a6faaae"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

cache = {} 
CACHE_TTL = 300 # 5 min cache
cache_time = {}

# Community Chat ke liye temporary storage
chat_messages = [
    {"user": "Sonu_Kumar", "msg": "Bhai Railway Group D ka form kab tak aayega?", "time": "10:45 AM"},
    {"user": "Admin_Rahul", "msg": "November tak umeed hai, taiyari jaari rakhein!", "time": "10:48 AM"}
]

# ===================== ROUTES FOR PWA =====================
@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(os.getcwd(), 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory(os.getcwd(), 'sw.js')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({"status": "AI V2 running", "api_key_set": bool(OPENROUTER_API_KEY)})

# ===================== JOBS & UPDATES =====================
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
            if "job" in href.lower():
                if len(jobs) < 15: jobs.append({"title": text, "link": href})
            elif "admit" in href.lower():
                if len(admits) < 15: admits.append({"title": text, "link": href})
        return jsonify({"jobs": jobs, "admits": admits})
    except:
        return jsonify({"jobs": [], "admits": []})

@app.route('/fetch_jobs', methods=['POST'])
def fetch_jobs():
    try:
        data = request.get_json()
        category = data.get('category', 'latest jobs')
        edu = data.get('edu', '')
        query = f"latest {category} vacancies for {edu} pass 2026 site:sarkariresult.com"
        headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
        payload = {'q': query, 'num': 20, 'gl': 'in'}
        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        return jsonify(response.json().get('organic', []))
    except Exception as e:
        return jsonify({"error": str(e)})

# ===================== RESUME GENERATOR =====================
@app.route('/generate_resume', methods=['POST'])
def generate_resume():
    try:
        data = request.form
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 20)
        pdf.cell(200, 10, txt="RESUME", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=f"Name: {data.get('name', 'N/A')}", ln=True)
        pdf.cell(200, 10, txt=f"Father's Name: {data.get('father', 'N/A')}", ln=True)
        pdf.cell(200, 10, txt=f"Education: {data.get('edu', 'N/A')}", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="SKILLS", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=data.get('skills', 'N/A'))
        output = io.BytesIO()
        pdf_content = pdf.output(dest='S').encode('latin-1')
        output.write(pdf_content)
        output.seek(0)
        response = make_response(output.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=resume.pdf'
        return response
    except Exception as e: return str(e)

# ===================== CHAT SYSTEM =====================
@app.route('/get_messages')
def get_messages(): return jsonify(chat_messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    chat_messages.append({"user": data.get('user', 'Guest'), "msg": data.get('msg', ''), "time": "Just Now"})
    return jsonify({"status": "sent"})

# ===================== NEW SMART AI LOGIC (V2) =====================
def fallback_ai(q):
    q = q.lower()
    if "hello" in q or "hi" in q: return "👋 Hello! Main Rozgar Hub AI assistant hoon, bolo kya help chahiye?"
    if "job" in q: return "📢 Latest jobs ke liye site ka home page check karo ya mujhe category batao."
    if "exam" in q: return "📚 Exam preparation ke liye syllabus follow karo aur daily practice karo."
    return "⚠️ Abhi saare AI models busy hain, thodi der baad try karo."

def call_model(model, question):
    try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a fast Hindi-English assistant for Rozgar Hub. Keep answers short."},
                {"role": "user", "content": question}
            ]
        }
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}, 
                            json=payload, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if "choices" in data: return data["choices"][0]["message"]["content"]
    except: return None
    return None

@app.route('/ask_ai', methods=['POST'])
def ask_ai():
    try:
        data = request.get_json()
        question = data.get('message') or data.get('question') or data.get('userMsg')
        if not question: return jsonify({"reply": "Sawal missing hai bhai!"})

        # CACHE CHECK
        if question in cache:
            if time.time() - cache_time[question] < CACHE_TTL:
                return jsonify({"reply": cache[question], "cached": True})

        if not OPENROUTER_API_KEY: return jsonify({"reply": fallback_ai(question)})

        # Parallel Models (Suggestion ke hisaab se)
        MODELS = ["openai/gpt-3.5-turbo", "mistralai/mistral-small", "google/gemini-2.0-flash-lite-preview-02-05:free"]

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(call_model, m, question) for m in MODELS]
            for f in as_completed(futures):
                result = f.result()
                if result:
                    cache[question] = result
                    cache_time[question] = time.time()
                    return jsonify({"reply": result, "active": "online_ai", "answer": result})

        return jsonify({"reply": fallback_ai(question), "active": "fallback"})
    except Exception as e:
        return jsonify({"reply": f"Server error: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)