# YouTube Frame Extractor API

A Flask-based REST API that extracts frames from YouTube videos and YouTube Shorts.

## Features

- Extract frames at 1 fps from YouTube videos
- Demo mode for testing without authentication
- Base64-encoded frame output
- Comprehensive error handling
- Production-ready with Gunicorn

## API Endpoints

### GET /
Health check and API documentation

### POST /extract
Extract frames from video

**Parameters:**
- `url`: YouTube video URL (string, optional if using demo mode)
- `demo`: Set to `true` for demo mode (boolean, optional)

**Example Requests:**

```bash
# Demo mode
curl -X POST https://your-app.railway.app/extract \
  -H "Content-Type: application/json" \
  -d '{"demo": true}'

# YouTube URL
curl -X POST https://your-app.railway.app/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/shorts/YOUR_VIDEO_ID"}'
```

**Response:**
```json
{
  "frames": ["base64string1", "base64string2", ...],
  "count": 5,
  "message": "Successfully extracted 5 frames"
}
```

## Deployment

This app is configured for Railway deployment with:
- Python 3.11
- FFmpeg system dependency
- Gunicorn WSGI server
- Automatic port binding

## Requirements

- Python 3.11+
- FFmpeg
- yt-dlp
- Flask
- Gunicorn