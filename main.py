from flask import Flask, request, jsonify
import os
import subprocess
import base64
import uuid
import logging
import shutil

# Setup logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "YouTube Frame Extractor API",
        "endpoints": {
            "extract": {
                "method": "POST",
                "description": "Extract frames from YouTube videos at 4fps for AI analysis",
                "parameters": {
                    "url": "YouTube video URL (required unless using demo mode)",
                    "demo": "Set to true for demo mode (optional)"
                },
                "response": {
                    "frames": "Array of base64-encoded JPEG images",
                    "count": "Number of frames extracted",
                    "message": "Status message"
                }
            }
        }
    })

@app.route("/extract", methods=["POST"])
def extract():
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.json
        url = data.get("url")
        demo_mode = data.get("demo", False)

        if not url and not demo_mode:
            return jsonify({"error": "Missing URL parameter"}), 400

        temp_id = str(uuid.uuid4())
        temp_dir = os.path.join(os.getcwd(), temp_id)
        os.makedirs(temp_dir, exist_ok=True)

        frames_pattern = os.path.join(temp_dir, "frame_%03d.jpg")

        try:
            if demo_mode:
                app.logger.info("Generating demo video...")
                demo_video_path = os.path.join(temp_dir, "demo_video.mp4")
                demo_cmd = [
                    "ffmpeg",
                    "-f", "lavfi",
                    "-i", "testsrc2=duration=5:size=320x240:rate=4",
                    "-pix_fmt", "yuv420p",
                    "-y",
                    demo_video_path
                ]
                subprocess.run(demo_cmd, capture_output=True, text=True, check=True, timeout=60)
                actual_video_path = demo_video_path
            else:
                app.logger.info(f"Downloading video from URL: {url}")
                video_path_template = os.path.join(temp_dir, "video.%(ext)s")
                download_cmd = [
                    "yt-dlp",
                    "-f", "best",
                    "--merge-output-format", "mp4",
                    "-o", video_path_template,
                    "--no-playlist",
                    "--user-agent", "Mozilla/5.0",
                    "--extractor-args", "youtube:player_client=web",
                    "--no-check-certificate",
                    url
                ]
                subprocess.run(download_cmd, capture_output=True, text=True, check=True, timeout=300)

                video_files = [f for f in os.listdir(temp_dir) if f.startswith("video.")]
                if not video_files:
                    return jsonify({"error": "Failed to download video"}), 500
                actual_video_path = os.path.join(temp_dir, video_files[0])

            app.logger.info("Starting frame extraction with ffmpeg...")
            ffmpeg_cmd = [
                "ffmpeg",
                "-i", actual_video_path,
                "-vf", "fps=4",
                "-y",
                frames_pattern
            ]
            subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=True, timeout=300)

            frame_files = [f for f in os.listdir(temp_dir) if f.startswith("frame_") and f.endswith(".jpg")]
            frame_files.sort()

            frames = []
            for frame_file in frame_files[:20]:
                frame_path = os.path.join(temp_dir, frame_file)
                with open(frame_path, "rb") as f:
                    frame_data = f.read()
                    frames.append(base64.b64encode(frame_data).decode("utf-8"))

            if not frames:
                return jsonify({"error": "No frames could be extracted from the video"}), 500

            return jsonify({
                "frames": frames,
                "count": len(frames),
                "message": f"Successfully extracted {len(frames)} frames"
            })

        except subprocess.TimeoutExpired:
            return jsonify({"error": "Processing timed out"}), 504

        except subprocess.CalledProcessError as e:
            app.logger.error(f"Subprocess error: {e}")
            return jsonify({"error": f"Subprocess failed: {str(e)}"}), 500

        except Exception as e:
            app.logger.error(f"General extraction error: {e}")
            return jsonify({"error": f"Internal server error: {str(e)}"}), 500

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    except Exception as e:
        app.logger.error(f"Request error: {e}")
        return jsonify({"error": "Invalid request format"}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        app.logger.info("yt-dlp is available")
    except Exception as e:
        app.logger.error(f"yt-dlp check failed: {e}")

    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        app.logger.info("ffmpeg is available")
    except Exception as e:
        app.logger.error(f"ffmpeg check failed: {e}")

    port = int(os.environ.get("PORT", 5000))
    app.logger.info(f"Starting API on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
