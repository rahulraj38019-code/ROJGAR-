import requests
from flask import Flask, render_template, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import os
import time
from bs4 import BeautifulSoup
from fpdf import FPDF 
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
CORS(app)

# ===================== CONFIG & CACHE =====================
SERPER_API_KEY = "675ec80f6858652b8add27fbe3ab09371a6faaae"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

cache = {} 
CACHE_TTL = 300 
cache_time = {}

# ===================== SMART BRAIN LOGIC (NEW) =====================

# 1. ChatGPT-Level System Instructions
SYSTEM_PROMPT = """
You are Rozgar Hub AI, a highly intelligent and professional assistant like ChatGPT.
Rules:
1. Always think deeply before answering.
2. If the user's question is unclear, ask for clarification.
3. Provide accurate, practical, and human-like answers in simple Hinglish.
4. If asked about coding, provide production-ready, clean code.
5. If the user asks a complex question, break it into steps.
6. Use emojis naturally to feel friendly but remain professional.
"""

# 2. Response Enhancer (Insaani touch ke liye)
def enhance_response(text):
    if not text: return text
    text = text.strip()
    if len(text) < 50:
        text += "\n\n📌 *Agar aapko aur detail chahiye to batao!*"
    return text

# 3. Local Fallback (Smart version)
def fallback_ai(q):
    q = q.lower()
    if "hello" in q or "hi" in q: return "👋 Namaste! Main Rozgar Hub AI hoon. Main aapki job search aur career mein kaise madad kar sakta hoon?"
    return "⚠️ Mere saare smart models abhi overload hain. Par main jaldi wapas aaunga. Tab tak aap site ke updates check kar sakte hain!"

# ===================== MODEL CALLING =====================

def call_smart_model(model, question):
    try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question}
            ],
            "temperature": 0.7 # Thodi creativity aur "intelligence" ke liye
        }
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}, 
                            json=payload, timeout=18)
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
        if not question: return jsonify({"reply": "Sawal likho bhai! 😊"})

        # CACHE CHECK
        if question in cache:
            if time.time() - cache_time[question] < CACHE_TTL:
                return jsonify({"reply": cache[question], "cached": True})

        if not OPENROUTER_API_KEY: return jsonify({"reply": fallback_ai(question)})

        # SMART MODELS (Video Suggestion ke mutabik high-level models)
        SMART_MODELS = [
            "openai/gpt-4o-mini",      # Sabse dimaag wala
            "anthropic/claude-3-haiku", # Reasoning expert
            "google/gemini-2.0-flash-lite-preview-02-05:free" # Fast + Smart
        ]

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(call_smart_model, m, question) for m in SMART_MODELS]
            for f in as_completed(futures):
                raw_result = f.result()
                if raw_result:
                    # Response ko enhance kar rahe hain
                    final_result = enhance_response(raw_result)
                    cache[question] = final_result
                    cache_time[question] = time.time()
                    return jsonify({"reply": final_result, "answer": final_result, "active": "smart_ai"})

        return jsonify({"reply": fallback_ai(question), "active": "fallback"})
    except Exception as e:
        return jsonify({"reply": f"Dimaag thak gaya hai (Error): {str(e)}"})

# ===================== BAAKI ROUTES (NO CHANGE) =====================

@app.route('/')
def index(): return render_template('index.html')

@app.route('/get_live_updates')
def get_live_updates():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get('https://sarkariresult.com.cm/', headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        jobs, admits = [], []
        all_links = soup.find_all('a')
        for link in all_links:
            text = link.text.strip(); href = link.get('href', '')
            if not href or len(text) < 10: continue
            if "job" in href.lower(): jobs.append({"title": text, "link": href})
            elif "admit" in href.lower(): admits.append({"title": text, "link": href})
        return jsonify({"jobs": jobs[:15], "admits": admits[:15]})
    except: return jsonify({"jobs": [], "admits": []})

@app.route('/generate_resume', methods=['POST'])
def generate_resume():
    try:
        data = request.form
        pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="RESUME", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Name: {data.get('name', 'N/A')}", ln=True)
        output = io.BytesIO()
        pdf_content = pdf.output(dest='S').encode('latin-1')
        output.write(pdf_content); output.seek(0)
        response = make_response(output.read())
        response.headers['Content-Type'] = 'application/pdf'
        return response
    except Exception as e: return str(e)

if __name__ == '__main__':
    app.run(debug=True)
