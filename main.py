
from flask import Flask, request, jsonify
import os
import subprocess
import base64
import uuid
import logging
import shutil

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "YouTube Frame Extractor API"})

@app.route("/extract", methods=["POST"])
def extract():
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.json
        url = data.get("url")
        if not url:
            return jsonify({"error": "Missing 'url' parameter"}), 400

        temp_id = str(uuid.uuid4())
        temp_dir = os.path.join("/tmp", temp_id)
        os.makedirs(temp_dir, exist_ok=True)

        video_path = os.path.join(temp_dir, "video.mp4")
        frames_pattern = os.path.join(temp_dir, "frame_%03d.jpg")

        # Download video with yt-dlp
        download_cmd = ["yt-dlp", "-f", "best", "-o", video_path, url]
        subprocess.run(download_cmd, check=True, capture_output=True, text=True)

        # Extract frames with ffmpeg at 4 fps
        ffmpeg_cmd = ["ffmpeg", "-i", video_path, "-vf", "fps=4", frames_pattern]
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)

        frames = []
        for filename in sorted(os.listdir(temp_dir)):
            if filename.endswith(".jpg"):
                with open(os.path.join(temp_dir, filename), "rb") as f:
                    frames.append(base64.b64encode(f.read()).decode("utf-8"))

        shutil.rmtree(temp_dir)

        if not frames:
            return jsonify({"error": "No frames extracted"}), 500

        return jsonify({"frames": frames, "count": len(frames), "message": "Frames extracted successfully"})

    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Subprocess error: {e.stderr}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
