from flask import Flask, request, jsonify
import subprocess
import os
import uuid
import base64
import shutil

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "service": "YouTube Frame Extractor API"})

@app.route("/extract", methods=["POST"])
def extract():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing 'url'"}), 400

    temp_dir = f"/tmp/{uuid.uuid4()}"
    os.makedirs(temp_dir, exist_ok=True)
    output_template = os.path.join(temp_dir, "frame_%03d.jpg")

    try:
        video_path = os.path.join(temp_dir, "video.mp4")
        subprocess.run([
            "yt-dlp", "-f", "best", "-o", video_path, url
        ], check=True)

        subprocess.run([
            "ffmpeg", "-i", video_path, "-vf", "fps=4", output_template
        ], check=True)

        frames = []
        for frame_file in sorted(os.listdir(temp_dir)):
            if frame_file.endswith(".jpg"):
                with open(os.path.join(temp_dir, frame_file), "rb") as f:
                    frames.append(base64.b64encode(f.read()).decode())

        return jsonify({"frames": frames, "count": len(frames)})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e)}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
