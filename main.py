import os
import requests
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from bs4 import BeautifulSoup
from time import time

app = Flask(__name__)
CORS(app)

SERPER_API_KEY = os.getenv("SERPER_API_KEY")

cache = {"data": None, "time": 0}
CACHE_DURATION = 300

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/manifest.json')
def manifest():
    return send_from_directory(os.getcwd(), 'manifest.json')

@app.route('/sw.js')
def sw():
    return send_from_directory(os.getcwd(), 'sw.js')

@app.route('/get_live_updates')
def get_live_updates():
    try:
        if cache["data"] and (time() - cache["time"] < CACHE_DURATION):
            return jsonify(cache["data"])

        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get('https://sarkariresult.com.cm/', headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        jobs, admits = [], []

        for link in soup.find_all('a'):
            text = link.text.strip()
            href = link.get('href', '')

            if not href or len(text) < 10:
                continue

            if ("job" in href.lower() or "recruit" in href.lower()) and len(jobs) < 15:
                jobs.append({"title": text, "link": href})

            elif ("admit" in href.lower() or "hall-ticket" in href.lower()) and len(admits) < 15:
                admits.append({"title": text, "link": href})

        data = {"jobs": jobs, "admits": admits}
        cache["data"] = data
        cache["time"] = time()

        return jsonify(data)

    except Exception:
        return jsonify({"jobs": [], "admits": []})

@app.route('/fetch_jobs', methods=['POST'])
def fetch_jobs():
    try:
        data = request.get_json()

        category = data.get('category', '')
        state = data.get('state', 'India')
        edu = data.get('edu', '')
        page = data.get('page', 1)

        query = f"{category} jobs for {edu} in {state}"

        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }

        payload = {
            'q': query,
            'num': 10,
            'start': (page - 1) * 10,
            'gl': 'in'
        }

        res = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        results = res.json().get('organic', [])

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run()