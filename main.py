import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
API_KEY = "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d" 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    # Broad search query for more results
    query = f"{data['interest']} jobs vacancy in {data['state']} 2026 official"
    
    headers = {
        'X-API-KEY': API_KEY,
        'Content-Type': 'application/json'
    }
    
    # 'num': 20 se zyada results aayenge
    payload = {'q': query, 'num': 20}
    
    try:
        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        results = response.json().get('organic', [])
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
  
