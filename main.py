from flask import Flask, request, jsonify
import subprocess
import os
import base64
import uuid
import shutil
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "OK", "message": "Railway API Running", "yt-dlp": check_yt_dlp(), "ffmpeg": check_ffmpeg()})

@app.route("/extract", methods=["POST"])
def extract():
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.json
        url = data.get("url")
        demo = data.get("demo", False)

        if not url and not demo:
            return jsonify({"error": "Missing 'url' or demo mode flag"}), 400

        temp_dir = os.path.join(os.getcwd(), str(uuid.uuid4()))
        os.makedirs(temp_dir, exist_ok=True)
        output_pattern = os.path.join(temp_dir, "frame_%03d.jpg")

        if demo:
            video_path = os.path.join(temp_dir, "demo.mp4")
            subprocess.run(["ffmpeg", "-f", "lavfi", "-i", "testsrc2=duration=5:size=320x240:rate=4", "-y", video_path], check=True)
        else:
            video_template = os.path.join(temp_dir, "video.%(ext)s")
            subprocess.run([
                "yt-dlp", "-f", "best", "--merge-output-format", "mp4",
                "-o", video_template, "--no-playlist", url
            ], check=True)
            files = [f for f in os.listdir(temp_dir) if f.startswith("video.")]
            if not files:
                return jsonify({"error": "yt-dlp download failed"}), 500
            video_path = os.path.join(temp_dir, files[0])

        subprocess.run([
            "ffmpeg", "-i", video_path, "-vf", "fps=4", "-y", output_pattern
        ], check=True)

        frames = []
        for frame_file in sorted(os.listdir(temp_dir)):
            if frame_file.endswith(".jpg"):
                with open(os.path.join(temp_dir, frame_file), "rb") as f:
                    frames.append(base64.b64encode(f.read()).decode('utf-8'))

        shutil.rmtree(temp_dir)

        if not frames:
            return jsonify({"error": "No frames extracted"}), 500

        return jsonify({"frames": frames, "count": len(frames)})

    except Exception as e:
        logging.error(f"Processing error: {e}")
        return jsonify({"error": str(e)}), 500

def check_yt_dlp():
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        return True
    except:
        return False

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except:
        return False

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
