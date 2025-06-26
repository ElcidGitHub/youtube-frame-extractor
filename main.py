from flask import Flask, request, jsonify
import os
import subprocess
import base64
import uuid
import logging
import shutil

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "YouTube Frame Extractor API",
        "endpoints": ["/extract"]
    })

@app.route("/extract", methods=["POST"])
def extract():
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.json
        url = data.get("url")
        if not url:
            return jsonify({"error": "Missing 'url' parameter"}), 400

        temp_dir = os.path.join(os.getcwd(), str(uuid.uuid4()))
        os.makedirs(temp_dir, exist_ok=True)
        video_template = os.path.join(temp_dir, "video.%(ext)s")

        try:
            subprocess.run([
                "yt-dlp", "-f", "best", "--merge-output-format", "mp4",
                "-o", video_template, "--no-playlist", url
            ], check=True, capture_output=True, text=True, timeout=300)

            video_files = [f for f in os.listdir(temp_dir) if f.startswith("video.")]
            if not video_files:
                return jsonify({"error": "Download failed, no video found."}), 500

            video_path = os.path.join(temp_dir, video_files[0])
            frame_pattern = os.path.join(temp_dir, "frame_%03d.jpg")

            subprocess.run([
                "ffmpeg", "-i", video_path, "-vf", "fps=4", "-y", frame_pattern
            ], check=True, capture_output=True, text=True, timeout=300)

            frames = []
            for frame_file in sorted([f for f in os.listdir(temp_dir) if f.startswith("frame_")]):
                with open(os.path.join(temp_dir, frame_file), "rb") as f:
                    frames.append(base64.b64encode(f.read()).decode("utf-8"))

            if not frames:
                return jsonify({"error": "No frames extracted."}), 500

            return jsonify({"frames": frames, "count": len(frames), "message": "Success"})

        except subprocess.CalledProcessError as e:
            return jsonify({"error": f"Subprocess failed: {e.stderr}"}), 500
        except subprocess.TimeoutExpired:
            return jsonify({"error": "Timeout during processing."}), 504
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
