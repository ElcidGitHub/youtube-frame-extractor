
# Railway YouTube Frame Extractor API

✅ Flask-based API for extracting frames from YouTube Shorts (4fps)

✅ Uses yt-dlp and ffmpeg

✅ Deploy on Railway with Nixpacks

## Endpoints:

- GET `/` - Health check
- POST `/extract` - Body: `{ "url": "https://youtube.com/shorts/xxx" }`

Returns Base64 frames as JSON array.

## Railway Setup:

✅ No Dockerfile needed  
✅ Nixpacks will auto-install Python, pip, ffmpeg, yt-dlp

