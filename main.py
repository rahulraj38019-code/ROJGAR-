
  import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Serper API Key
API_KEY = "268aa2e751d03f3d61ffa0fe6b46cd80bf6ec73d" 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    data = request.json
    interest = data.get('interest')
    state = data.get('state')
    page = data.get('page', 1) 
    
    # Query ko thoda broad rakha hai zyada results ke liye
    query = f"{interest} latest vacancy in {state} 2026 govt private"
    
    headers = {
        'X-API-KEY': API_KEY,
        'Content-Type': 'application/json'
    }
    
    # 'page' parameter agle results dikhayega
    payload = {'q': query, 'num': 20, 'page': page}
    
    try:
        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        results = response.json().get('organic', [])
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

