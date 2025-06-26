# YouTube Frame Extractor API (Railway Deployment)

This Flask app extracts frames from YouTube videos for AI processing.

## Endpoints

- **GET /** → Health check
- **POST /extract** → Provide JSON:

```json
{
  "url": "https://youtube.com/shorts/xxxx",
  "demo": false
}
