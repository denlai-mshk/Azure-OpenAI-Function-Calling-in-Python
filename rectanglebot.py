from flask import Flask, request, render_template
import requests
import json

app = Flask(__name__)

AZURE_OPENAI_API_URL = "https://<your-resource-name>.openai.azure.com/openai/deployments/<deployment-id>/chat/completions?api-version=2024-02-15-preview"
AZURE_OPENAI_API_KEY = "<your-api-key>"
BACKEND_LOGIC_URL = "http://localhost:5001/calculate-area"

def call_openai_api(messages):
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_API_KEY
    }
    data = {
        "model": "gpt-4o",
        "messages": messages,
        "functions": [
            {
                "name": "calculate_area",
                "description": "Calculates the area of a rectangle given the length and width.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "length": {"type": "number", "description": "The length of the rectangle"},
                        "width": {"type": "number", "description": "The width of the rectangle"}
                    },
                    "required": ["length", "width"]
                }
            }
        ],
        "function_call": "auto"
    }
    response = requests.post(AZURE_OPENAI_API_URL, headers=headers, json=data)
    
    if response.status_code == 401:
        return "Unauthorized. Access token is missing, invalid, audience is incorrect, or has expired."
    
    return response.json()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/interact', methods=['POST'])
def interact():
    user_input = request.json.get('user_input')
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Your task is to collect the necessary parameters from the user and construct a function call without performing the calculation yourself."},
        {"role": "user", "content": user_input}
    ]
    openai_response = call_openai_api(messages)
    
    if 'choices' not in openai_response or not openai_response['choices']:
        return "Invalid response from OpenAI API", 500
    
    function_call = openai_response['choices'][0].get('message', {}).get('function_call')
    
    if not function_call:
        content = openai_response['choices'][0].get('message', {}).get('content', 'No function call found')
        return content
    
    if function_call['name'] == 'calculate_area':
        params = json.loads(function_call['arguments'])
        # Call the backend logic
        backend_response = requests.post(BACKEND_LOGIC_URL, json=params)
        
        if backend_response.status_code != 200:
            return "Error calling backend logic", 500
        
        area = backend_response.json().get('area')
        return f"The area of the rectangle is {area}"
    
    return json.dumps(function_call)

if __name__ == '__main__':
    app.run(debug=True)