import requests
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os, json, time, io
from bs4 import BeautifulSoup
from fpdf import FPDF
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract

app = Flask(__name__)
CORS(app)

# ================= CONFIG =================
SERPER_API_KEY = "YOUR_SERPER_KEY"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

UPLOAD_FOLDER = "uploads"
CHAT_FOLDER = "saved_chats"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHAT_FOLDER, exist_ok=True)

chat_messages = [
    {"user": "Admin", "msg": "Welcome to VidyaJobs AI", "time": "10:00 AM"}
]

# ================= UTIL =================
def chat_file(uid):
    return f"{CHAT_FOLDER}/{uid}.json"

def load_chat(uid):
    path = chat_file(uid)
    if os.path.exists(path):
        return json.load(open(path, "r", encoding="utf-8"))
    return []

def save_chat(uid, data):
    with open(chat_file(uid), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def serper(query):
    try:
        headers = {"X-API-KEY": SERPER_API_KEY}
        res = requests.post(
            "https://google.serper.dev/search",
            headers=headers,
            json={"q": query, "gl": "in"},
            timeout=10
        )
        return res.json().get("organic", [])
    except:
        return []

# ================= ROUTES =================
@app.route("/")
def home():
    return render_template("index.html")

# ===== AI =====
@app.route("/ask_ai_v10", methods=["POST"])
def ai():
    data = request.json
    msg = data.get("message", "")
    uid = data.get("uid", "guest")

    history = load_chat(uid)

    live = ""
    if any(k in msg.lower() for k in ["job","result","news","vacancy"]):
        live_data = serper(msg)
        live = "\n".join([x["title"] for x in live_data[:5]])

    prompt = f"User query: {msg}\nLive data:\n{live}"

    reply = f"AI Reply: {msg}"

    history.append({"role":"user","content":msg})
    history.append({"role":"assistant","content":reply})

    save_chat(uid, history)

    return jsonify({"reply": reply})

# ===== JOBS =====
@app.route("/fetch_jobs", methods=["POST"])
def jobs():
    data = request.json
    q = data.get("category","jobs")
    return jsonify(serper(q))

# ===== CHAT =====
@app.route("/save_chat", methods=["POST"])
def save():
    d = request.json
    save_chat(d["uid"], d["chats"])
    return jsonify({"ok":True})

@app.route("/load_chat", methods=["POST"])
def load():
    uid = request.json["uid"]
    return jsonify({"chats": load_chat(uid)})

@app.route("/recent_chats")
def recent():
    files = os.listdir(CHAT_FOLDER)
    return jsonify({"users":[f.replace(".json","") for f in files]})

@app.route("/delete_chat", methods=["POST"])
def delete():
    uid = request.json["uid"]
    path = chat_file(uid)
    if os.path.exists(path):
        os.remove(path)
    return jsonify({"ok":True})

# ===== COMMUNITY =====
@app.route("/get_messages")
def msgs():
    return jsonify(chat_messages)

@app.route("/send_message", methods=["POST"])
def send():
    d = request.json
    chat_messages.append({
        "user": d.get("user","Guest"),
        "msg": d.get("msg",""),
        "time": time.strftime("%I:%M %p")
    })
    return jsonify({"ok":True})

# ===== OCR =====
@app.route("/ocr", methods=["POST"])
def ocr():
    file = request.files["file"]
    img = Image.open(file)
    text = pytesseract.image_to_string(img)
    return jsonify({"text": text})

# ===== PDF =====
@app.route("/read_pdf", methods=["POST"])
def pdf():
    file = request.files["file"]
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    reader = PdfReader(path)
    text = "".join([p.extract_text() or "" for p in reader.pages])

    return jsonify({"text": text[:12000]})

# ===== RESUME =====
@app.route("/generate_resume", methods=["POST"])
def resume():
    d = request.form

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, "VIDYAJOBS RESUME", ln=True)

    for k,v in d.items():
        pdf.cell(200, 10, f"{k}: {v}", ln=True)

    out = io.BytesIO()
    out.write(pdf.output(dest="S").encode("latin-1"))
    out.seek(0)

    return send_file(out, download_name="resume.pdf", as_attachment=True)

# ===== LIVE =====
@app.route("/get_live_updates")
def live():
    try:
        r = requests.get("https://sarkariresult.com.cm/", timeout=10)
        soup = BeautifulSoup(r.text,"html.parser")

        jobs, admits = [], []

        for a in soup.find_all("a"):
            t = a.text.strip()
            h = a.get("href","")
            if "admit" in h:
                admits.append({"title":t,"link":h})
            else:
                jobs.append({"title":t,"link":h})

        return jsonify({"jobs":jobs[:10],"admits":admits[:10]})
    except:
        return jsonify({"jobs":[],"admits":[]})

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)