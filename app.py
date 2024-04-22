from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
import os
import json
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Assuming you're okay with uploads being stored in the "uploads" folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def upload_file():
    return render_template('upload.html')

@app.route('/uploader', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        result = analyze_image(filepath)
        # Ensure result is a dictionary
        if not isinstance(result, dict):
            return "Error processing results", 500
        return render_template('result.html', result=result, filename=filename)

def analyze_image(image_path):
    api_key = os.getenv("OPENAI_API_KEY")

    with open('system_prompt.txt', 'r') as file:
        system_prompt = file.read()     
    base64_image = encode_image(image_path)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "gpt-4-turbo",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            }, 
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": "Analiza la imagen y responde solo con la información en formato JSON"
                },
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
                }
            ]
            }
        ],
        "max_tokens": 300,
        "response_format": {"type": "json_object"}
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    response_data = response.json()['choices'][0]['message']['content']
    print(response_data)
    
    # Check if response_data is a string and convert it to a dictionary if necessary
    if isinstance(response_data, str):
        response_data = json.loads(response_data)
    
    return response_data

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

if __name__ == '__main__':
    app.run(debug=True)
