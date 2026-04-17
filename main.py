import requests
from flask import Flask, render_template, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import os
from bs4 import BeautifulSoup
from fpdf import FPDF # Resume generation ke liye
import io

app = Flask(__name__)
CORS(app)

# --- API KEYS ---
SERPER_API_KEY = "675ec80f6858652b8add27fbe3ab09371a6faaae"

# Community Chat ke liye temporary storage
chat_messages = [
    {"user": "Sonu_Kumar", "msg": "Bhai Railway Group D ka form kab tak aayega?", "time": "10:45 AM"},
    {"user": "Admin_Rahul", "msg": "November tak umeed hai, taiyari jaari rakhein!", "time": "10:48 AM"}
]

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(os.getcwd(), 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory(os.getcwd(), 'sw.js')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_live_updates')
def get_live_updates():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
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
    except:
        return jsonify({"jobs": [], "admits": []})

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
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="EXPERIENCE", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=data.get('exp', 'N/A'))
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

@app.route('/get_messages')
def get_messages():
    return jsonify(chat_messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    new_msg = {"user": data.get('user', 'Guest'), "msg": data.get('msg', ''), "time": "Just Now"}
    chat_messages.append(new_msg)
    if "?" in new_msg['msg']:
        chat_messages.append({"user": "Admin_Bot", "msg": "Aapka sawal mil gaya hai!", "time": "Just Now"})
    return jsonify({"status": "sent"})

# --- AI ROUTE WITH AUTO-FALLBACK SYSTEM ---
@app.route('/ask_ai', methods=['POST'])
def ask_ai():
    try:
        data = request.get_json()
        question = data.get('message') or data.get('question') or data.get('userMsg')
        
        if not question:
            return jsonify({"reply": "Bhai, sawal toh likho!", "answer": "Bhai, sawal toh likho!"})

        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return jsonify({"reply": "API Key missing in Render!", "answer": "API Key missing!"})

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Priority List: 1. Gemini, 2. Llama, 3. Mistral
        models = [
            "google/gemini-2.0-flash-lite-preview-02-05:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "mistralai/mistral-7b-instruct:free"
        ]

        for model_name in models:
            try:
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": "You are Rozgar Hub AI Assistant. Help users in Hinglish."},
                        {"role": "user", "content": str(question)}
                    ]
                }
                
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions", 
                    headers=headers, 
                    json=payload, 
                    timeout=15
                )
                
                result = response.json()
                
                if 'choices' in result and len(result['choices']) > 0:
                    answer = result['choices'][0]['message']['content']
                    # Dono keys bhej rahe hain compatibility ke liye
                    return jsonify({"answer": answer, "reply": answer, "active_model": model_name})
                
                # Agar choice nahi mili toh agla model try karo
                continue
                
            except:
                continue # Network error ya timeout par agla model try karega

        return jsonify({"reply": "Bhai, abhi saare AI models busy hain. 1 min baad try karo.", "answer": "All models busy."})
            
    except Exception as e:
        return jsonify({"reply": f"Backend Error: {str(e)}", "answer": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
