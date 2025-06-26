# YouTube Frame Extractor API for Railway

## Overview
A simple Flask API to extract frames from YouTube Shorts for AI analysis.

## Endpoints
- `GET /` → Health Check
- `POST /extract` → Requires JSON body:
```
{
  "url": "https://youtube.com/shorts/XXXXXX",
  "demo": false
}
```

## Railway Deployment Notes
- Python 3.11
- FFmpeg and yt-dlp installed via Nixpacks
- Start command managed by Gunicorn

## Postman Test Example
```
POST https://your-railway-url.app/extract
Body:
{
  "url": "https://youtube.com/shorts/XXXXXX"
}
Content-Type: application/json
```