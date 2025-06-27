# YouTube Frame Extractor API (Railway Deployment)

### ✅ Features:
- Flask API with `/extract` endpoint.
- Uses yt-dlp + ffmpeg (installed via Nixpacks) to download YouTube Shorts and extract frames at 4fps.
- No Dockerfile needed. Nixpacks will auto-build.

---

### ✅ Deployment Steps (Railway):

1. Upload this project to your GitHub.
2. On Railway, create a **new project from GitHub**.
3. Railway auto-detects Nixpacks, no Dockerfile needed.
4. Confirm Build Commands:
   - **Setup**: Installs ffmpeg and Python 3.11
   - **Install**: pip install -r requirements.txt
   - **Start**: gunicorn --bind 0.0.0.0:$PORT main:app

---

### ✅ Testing:

POST to:
```
https://your-railway-app-url/extract
```
Body (JSON):
```
{
  "url": "https://youtube.com/shorts/yourshortid"
}
```

or use demo mode:

```
{ "demo": true }
```

---

✅ This build is Railway + Nixpacks tested for yt-dlp and ffmpeg extraction.