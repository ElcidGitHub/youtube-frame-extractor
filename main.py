from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"status": "healthy", "message": "API running on Railway!"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)