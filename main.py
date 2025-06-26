from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "Railway Nixpacks Flask app with ffmpeg and yt-dlp working!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
