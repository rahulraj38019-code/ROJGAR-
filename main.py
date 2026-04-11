import requests
from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

API_KEY = "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        interest = data.get('interest', 'jobs')
        state = data.get('state', 'India')
        page = data.get('page', 1)
        query = f"{interest} latest vacancy in {state} 2026"
        headers = {'X-API-KEY': API_KEY, 'Content-Type': 'application/json'}
        payload = {'q': query, 'num': 10, 'page': page}
        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        return jsonify(response.json().get('organic', []))
    except Exception as e:
        return jsonify([])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
