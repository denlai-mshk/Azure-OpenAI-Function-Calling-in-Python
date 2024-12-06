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