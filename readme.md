# Azure OpenAI Function Calling in Python
![cover](/cover.png)

This GitHub repo shows you how to leverage the Azure OpenAI function calling.

### Step 1: Set Up Your Python Environment

1. **Create a Project Directory**:
   ```bash
   mkdir funccall_demo
   cd funccall_demo
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment**:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install Required Packages**:
   ```bash
   pip install Flask requests
   ```

### Step 2: Create RectangleBot (Frontend)

1. **Create `rectanglebot.py`**:
    Change the values of **your-api-key**, **deployment-id** and **your-resource-name**

   ```python
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
   ```

2. **Create Templates Directory and HTML File**:
   - Create a directory named `templates` in the project directory.
   - Inside the `templates` directory, create a file named `index.html`.

3. **Create `index.html`**:
   ```html
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>RectangleBot</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background-color: #f0f0f0;
            }
            .chat-container {
                width: 400px;
                background-color: white;
                padding: 20px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            }
            .chat-box {
                width: 100%;
                height: 300px;
                border: 1px solid #ccc;
                padding: 10px;
                overflow-y: auto;
                margin-bottom: 10px;
                border-radius: 4px;
            }
            .input-box {
                display: flex;
            }
            .input-box input {
                flex: 1;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            .input-box button {
                padding: 10px;
                border: none;
                background-color: #007bff;
                color: white;
                border-radius: 4px;
                margin-left: 10px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-box" id="chat-box"></div>
            <div class="input-box">
                <input type="text" id="user-input" value="Calculate the area of a rectangle with length 5 and width 3">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
        <script>
            function sendMessage() {
                const userInput = document.getElementById('user-input').value;
                const chatBox = document.getElementById('chat-box');
                chatBox.innerHTML += `<p><strong>You:</strong> ${userInput}</p>`;
                fetch('/interact', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ user_input: userInput })
                })
                .then(response => response.text())
                .then(data => {
                    chatBox.innerHTML += `<p><strong>RectangleBot:</strong> ${data}</p>`;
                    chatBox.scrollTop = chatBox.scrollHeight;
                });
                document.getElementById('user-input').value = '';
            }

            document.getElementById('user-input').addEventListener('keypress', function(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
   ```

### Step 3: Create BackendLogic (Backend)

1. **Create `backendlogic.py`**:
   ```python
    from flask import Flask, request, jsonify

    app = Flask(__name__)

    def calculate_area(length, width):
        # Add 20 intentionally, to show the value is calculated by backendlogic, not by openai model.
        return ((length * width) + 20)

    @app.route('/calculate-area', methods=['POST'])
    def calculate_area_endpoint():
        data = request.get_json()
        length = data.get('length')
        width = data.get('width')
        if length is None or width is None:
            return jsonify({"error": "Missing length or width"}), 400
        area = calculate_area(length, width)
        return jsonify({"area": area})

    if __name__ == '__main__':
        app.run(debug=True, port=5001)
   ```

### Step 4: Run the Applications

1. **Start RectangleBot**:
   ```bash
   python rectanglebot.py
   ```

2. **Start BackendLogic**:
   ```bash
   python backendlogic.py
   ```

### Step 5: Test the Applications

1. **Open a Web Browser** and go to `http://127.0.0.1:5000`.
2. **Interact with RectangleBot** using the chat interface.
### Explanation

- **RectangleBot**: Collects user inputs and constructs the function call using the Azure OpenAI API.
- **BackendLogic**: Receives the function call and performs the actual calculation. We add +20 to the calculation intentionally for showcase the calculation is by the backendlogic.py, not by OpenAI model.

This setup ensures that your application collects user inputs, constructs the function call, and triggers the backend logic to perform the calculation.
![test](/test.jpg)

### References
[Get started with Azure OpenAI with Assistants and function calling](https://learn.microsoft.com/en-us/azure/developer/javascript/ai/get-started-app-chat-assistants-function-calling?tabs=github-codespaces)

[How to use function calling with Azure OpenAI Service](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/function-calling)