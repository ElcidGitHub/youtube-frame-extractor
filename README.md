# YouTube Shorts Frame Extractor API (Railway Deployment)

This is a simple Flask API for extracting video frames from YouTube Shorts or long YouTube videos.  
It uses **yt-dlp** for downloading videos and **FFmpeg** for extracting frames.

Built and deployed for Railway.

---

## ✅ Features

- Downloads YouTube videos (including Shorts) via **yt-dlp**
- Extracts frames at **4 frames per second (FPS)** for AI analysis
- Outputs frames as **Base64-encoded JPEGs** (ideal for sending to Gemini Vision API or Google Vision AI)
- Offers a **demo mode** that generates test frames without downloading
- Lightweight and production-ready with Gunicorn
- Health check endpoint for uptime monitoring

---

## ✅ API Endpoints

### Health Check

**GET /**  
Returns a JSON status confirming the API is running.

---

### Frame Extraction

**POST /extract**

#### Parameters (JSON):

| Parameter | Type   | Required | Description                          |
| --------- | ------ | -------- | ------------------------------------ |
| `url`     | string | Yes (unless using demo mode) | Full YouTube Shorts or YouTube video URL |
| `demo`    | bool   | Optional | If `true`, runs a test demo without YouTube download |

---

### ✅ Example CURL Commands:

**Demo Mode Example:**
```bash
curl -X POST https://brilliant-reflection.railway.app/extract \
  -H "Content-Type: application/json" \
  -d '{"demo": true}'
