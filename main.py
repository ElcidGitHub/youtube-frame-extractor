from flask import Flask, request, jsonify, send_file
import subprocess
import os
import uuid
import shutil

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"service": "YouTube Frame Extractor API", "status": "healthy"})

@app.route("/download", methods=["GET"])
def download_video():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    temp_dir = f"/tmp/{uuid.uuid4()}"
    os.makedirs(temp_dir, exist_ok=True)
    video_path = os.path.join(temp_dir, "video.mp4")

    try:
        subprocess.run([
            "yt-dlp",
            "-f", "best",
            "-o", video_path,
            url
        ], check=True)

        if not os.path.exists(video_path) or os.path.getsize(video_path) < 1024:
            return jsonify({"error": "Download failed or file too small."}), 500

        return send_file(video_path, mimetype='video/mp4', as_attachment=True)
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"yt-dlp error: {str(e)}"}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.route("/extract", methods=["POST"])
def extract_frames():
    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing 'url' in POST body"}), 400

    temp_dir = f"/tmp/{uuid.uuid4()}"
    os.makedirs(temp_dir, exist_ok=True)
    video_path = os.path.join(temp_dir, "video.mp4")
    frame_pattern = os.path.join(temp_dir, "frame_%03d.jpg")

    try:
        subprocess.run([
            "yt-dlp",
            "-f", "best",
            "-o", video_path,
            url
        ], check=True)

        subprocess.run([
            "ffmpeg",
            "-i", video_path,
            "-vf", "fps=4",
            frame_pattern
        ], check=True)

        frames = [f for f in os.listdir(temp_dir) if f.endswith(".jpg")]

        return jsonify({
            "frames_count": len(frames),
            "frames": frames
        })
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Processing error: {str(e)}"}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
