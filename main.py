from flask import Flask, request, jsonify
import os
import subprocess
import base64
import uuid
import shutil
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "YouTube Frame Extractor API"})

@app.route("/extract", methods=["POST"])
def extract():
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.json
        url = data.get("url")
        demo = data.get("demo", False)

        if not url and not demo:
            return jsonify({"error": "Missing YouTube URL or demo flag"}), 400

        temp_id = str(uuid.uuid4())
        temp_dir = os.path.join(os.getcwd(), temp_id)
        os.makedirs(temp_dir, exist_ok=True)
        frames_pattern = os.path.join(temp_dir, "frame_%03d.jpg")

        if demo:
            demo_video = os.path.join(temp_dir, "demo.mp4")
            cmd = ["ffmpeg", "-f", "lavfi", "-i", "testsrc2=duration=5:size=320x240:rate=4", "-pix_fmt", "yuv420p", "-y", demo_video]
            subprocess.run(cmd, check=True, capture_output=True)
            input_video = demo_video
        else:
            video_template = os.path.join(temp_dir, "video.%(ext)s")
            download_cmd = ["yt-dlp", "-f", "best", "--merge-output-format", "mp4", "-o", video_template, "--no-playlist", url]
            subprocess.run(download_cmd, check=True, capture_output=True)
            files = [f for f in os.listdir(temp_dir) if f.startswith("video.")]
            if not files:
                return jsonify({"error": "Video download failed."}), 500
            input_video = os.path.join(temp_dir, files[0])

        ffmpeg_cmd = ["ffmpeg", "-i", input_video, "-vf", "fps=4", "-y", frames_pattern]
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

        frames = []
        for f in sorted(os.listdir(temp_dir)):
            if f.endswith(".jpg"):
                with open(os.path.join(temp_dir, f), "rb") as img:
                    frames.append(base64.b64encode(img.read()).decode())

        shutil.rmtree(temp_dir)

        return jsonify({
            "frames": frames,
            "count": len(frames),
            "message": f"{len(frames)} frames extracted."
        })

    except subprocess.CalledProcessError as e:
        logging.error(f"Subprocess error: {e.stderr}")
        return jsonify({"error": f"Subprocess failed: {str(e)}"}), 500
    except Exception as ex:
        logging.error(f"General error: {str(ex)}")
        return jsonify({"error": f"Internal server error: {str(ex)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)