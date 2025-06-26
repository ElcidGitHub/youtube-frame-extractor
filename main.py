
from flask import Flask, request, jsonify
import subprocess
import logging

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "YouTube Frame Extractor Running"})

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

if __name__ == "__main__":
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        logging.info("yt-dlp available")
    except Exception as e:
        logging.error(f"yt-dlp check failed: {e}")

    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        logging.info("ffmpeg available")
    except Exception as e:
        logging.error(f"ffmpeg check failed: {e}")

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
