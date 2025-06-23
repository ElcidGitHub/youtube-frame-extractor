from flask import Flask, request, jsonify
import os
import subprocess
import base64
import uuid
import logging
import shutil

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint to verify the service is running"""
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
        },
        "demo_usage": {
            "description": "Test the API without YouTube authentication",
            "example": {"demo": True}
        }
    })

@app.route("/extract", methods=["POST"])
def extract():
    """Extract frames from YouTube video URL"""
    try:
        # Validate request data
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.json
        url = data.get("url")
        demo_mode = data.get("demo", False)
        
        if not url and not demo_mode:
            return jsonify({"error": "Missing URL parameter"}), 400
        
        if url and (not isinstance(url, str) or not url.strip()):
            return jsonify({"error": "URL must be a non-empty string"}), 400
        
        # Create unique temporary directory
        temp_id = str(uuid.uuid4())
        temp_dir = os.path.join(os.getcwd(), temp_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            frames_pattern = os.path.join(temp_dir, "frame_%03d.jpg")
            
            app.logger.debug(f"Created temporary directory: {temp_dir}")
            
            if demo_mode:
                # Create a simple demo video using ffmpeg
                app.logger.info("Creating demo video...")
                demo_video_path = os.path.join(temp_dir, "demo_video.mp4")
                
                # Create a 5-second test video with changing colors
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
                app.logger.info("Demo video created successfully")
                
            else:
                # Download video using yt-dlp
                app.logger.info(f"Processing video URL: {url}")
                video_path = os.path.join(temp_dir, "video.%(ext)s")
                
                download_cmd = [
                    "yt-dlp", 
                    "-f", "best",  # Get best quality
                    "--merge-output-format", "mp4",  # Ensure MP4 output
                    "-o", video_path,
                    "--no-playlist",  # Only download single video
                    "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "--extractor-args", "youtube:player_client=web",
                    "--no-check-certificate",
                    url
                ]
                
                try:
                    download_result = subprocess.run(
                        download_cmd, 
                        capture_output=True, 
                        text=True, 
                        check=True,
                        timeout=300  # 5 minute timeout
                    )
                    
                    app.logger.debug(f"yt-dlp output: {download_result.stdout}")
                    
                    # Find the downloaded video file
                    video_files = [f for f in os.listdir(temp_dir) if f.startswith("video.")]
                    if not video_files:
                        return jsonify({"error": "Failed to download video"}), 500
                    
                    actual_video_path = os.path.join(temp_dir, video_files[0])
                    app.logger.info(f"Video downloaded successfully: {actual_video_path}")
                    
                except subprocess.CalledProcessError as e:
                    if "Sign in to confirm you're not a bot" in str(e.stderr):
                        return jsonify({
                            "error": "YouTube requires authentication. Try using demo mode by adding '\"demo\": true' to your request.",
                            "suggestion": "Use demo mode to test the frame extraction functionality",
                            "demo_example": {"url": "", "demo": True}
                        }), 403
                    else:
                        raise
            
            # Extract frames using ffmpeg (4 frames per second for better analysis)
            app.logger.info("Starting frame extraction...")
            ffmpeg_cmd = [
                "ffmpeg",
                "-i", actual_video_path,
                "-vf", "fps=4",  # Extract 4 frames per second for pacing/transitions
                "-y",  # Overwrite output files
                frames_pattern
            ]
            
            ffmpeg_result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300  # 5 minute timeout
            )
            
            app.logger.debug(f"ffmpeg output: {ffmpeg_result.stderr}")
            
            # Read frames and convert to base64
            frames = []
            frame_files = [f for f in os.listdir(temp_dir) if f.startswith("frame_") and f.endswith(".jpg")]
            frame_files.sort()  # Ensure proper ordering
            
            app.logger.info(f"Found {len(frame_files)} frames")
            
            # Process all frames for comprehensive analysis (up to 20 for performance)
            for frame_file in frame_files[:20]:
                frame_path = os.path.join(temp_dir, frame_file)
                try:
                    with open(frame_path, "rb") as f:
                        frame_data = f.read()
                        encoded_frame = base64.b64encode(frame_data).decode("utf-8")
                        frames.append(encoded_frame)
                        app.logger.debug(f"Encoded frame: {frame_file}")
                except Exception as e:
                    app.logger.error(f"Error reading frame {frame_file}: {str(e)}")
                    continue
            
            if not frames:
                return jsonify({"error": "No frames could be extracted from the video"}), 500
            
            app.logger.info(f"Successfully extracted {len(frames)} frames")
            
            response_data = {
                "frames": frames,
                "count": len(frames),
                "message": f"Successfully extracted {len(frames)} frames"
            }
            
            if demo_mode:
                response_data["demo"] = True
                response_data["message"] += " (demo mode)"
            
            return jsonify(response_data)
            
        except subprocess.TimeoutExpired:
            app.logger.error("Video processing timed out")
            return jsonify({"error": "Video processing timed out. Please try with a shorter video."}), 504
            
        except subprocess.CalledProcessError as e:
            app.logger.error(f"Command failed: {e.cmd}")
            app.logger.error(f"Return code: {e.returncode}")
            app.logger.error(f"Stdout: {e.stdout}")
            app.logger.error(f"Stderr: {e.stderr}")
            
            if "yt-dlp" in str(e.cmd):
                return jsonify({"error": "Failed to download video. Please check if the URL is valid and accessible."}), 400
            elif "ffmpeg" in str(e.cmd):
                return jsonify({"error": "Failed to extract frames from video. The video format may not be supported."}), 500
            else:
                return jsonify({"error": f"Processing failed: {str(e)}"}), 500
                
        except Exception as e:
            app.logger.error(f"Unexpected error during processing: {str(e)}")
            return jsonify({"error": f"Internal processing error: {str(e)}"}), 500
            
        finally:
            # Clean up temporary directory
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    app.logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                app.logger.error(f"Failed to clean up temporary directory {temp_dir}: {str(e)}")
    
    except Exception as e:
        app.logger.error(f"Request handling error: {str(e)}")
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
    # Check if required tools are available
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
        app.logger.info("yt-dlp is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        app.logger.error("yt-dlp is not installed or not available in PATH")
    
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        app.logger.info("ffmpeg is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        app.logger.error("ffmpeg is not installed or not available in PATH")
    
    app.logger.info("Starting YouTube Frame Extractor API on port 5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
