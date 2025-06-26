from flask import Flask, request, jsonify
import os
import subprocess
import uuid
import base64
import shutil

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "service": "YouTube Frame Extractor API"})

@app.route("/extract", methods=["POST"])
def extract():
    try:
        data = request.json
        url = data.get("url")
        demo_mode = data.get("demo", False)

        if not url and not demo_mode:
            return jsonify({"error": "Missing YouTube URL or demo mode"}), 400

        temp_id = str(uuid.uuid4())
        temp_dir = os.path.join("/tmp", temp_id)
        os.makedirs(temp_dir, exist_ok=True)
        frames_pattern = os.path.join(temp_dir, "frame_%03d.jpg")

        try:
            if demo_mode:
                demo_path = os.path.join(temp_dir, "demo.mp4")
                subprocess.run([
                    "ffmpeg", "-f", "lavfi", "-i", "testsrc2=duration=5:size=320x240:rate=2",
                    "-pix_fmt", "yuv420p", "-y", demo_path
                ], check=True)
                video_path = demo_path
            else:
                video_template = os.path.join(temp_dir, "video.%(ext)s")
                subprocess.run([
                    "yt-dlp", "-f", "best", "--merge-output-format", "mp4",
                    "-o", video_template, "--no-playlist", url
                ], check=True)
                files = [f for f in os.listdir(temp_dir) if f.startswith("video.")]
                if not files:
                    return jsonify({"error": "Video download failed"}), 500
                video_path = os.path.join(temp_dir, files[0])

            subprocess.run([
                "ffmpeg", "-i", video_path, "-vf", "fps=4", "-y", frames_pattern
            ], check=True)

            frames = []
            for f in sorted(os.listdir(temp_dir)):
                if f.startswith("frame_") and f.endswith(".jpg"):
                    with open(os.path.join(temp_dir, f), "rb") as img:
                        frames.append(base64.b64encode(img.read()).decode())

            if not frames:
                return jsonify({"error": "No frames extracted"}), 500

            return jsonify({"frames": frames, "count": len(frames)})
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)