from flask import Flask, request, jsonify
from search_tube.engine import Engine

app = Flask(__name__)

engine = Engine()

@app.route('/', methods=['POST'])
def receive_urls():
    try:
        # Get the URL-encoded data
        urls_data = request.form.get('urls')
        if urls_data:
            urls = eval(urls_data)  # Convert string back to list (use json.loads if it's JSON)
            engine.load_urls(urls)
            return jsonify({"status": "success", "received_urls": urls}), 200
        else:
            return jsonify({"status": "error", "message": "No URLs provided"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555)
