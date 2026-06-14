# Meme Shorts Generator — Build Plan

## Goal
Automated YouTube Shorts pipeline: fetch memes from Reddit → OCR text → TTS voiceover → Minecraft parkour background + reaction meme images + sound effects → render 30-60s Shorts.

**Everything runs on this Windows PC. No VPS.**

## What's Already Done
- ✅ n8n installed and running on `http://localhost:5678` (also via Tailscale `http://100.83.156.25:5678`)
- ✅ n8n API Key works
- ✅ Python 3.12 + pip installed
- ✅ FFmpeg 8.1.1 installed
- ✅ edge-tts installed
- ✅ Flask + requests installed
- ✅ Basic workflow "Meme Shorts Generator" in n8n (ID: `Qhy8bDVbsWUZGQVY`) — needs replacement
- ✅ Reaction meme images in `assets/reactions/` (Speed, Pikachu, Skull, etc.)
- ✅ Sound effects in `assets/sounds/` (vine_boom, laugh, fail, oof, bruh, pop, drum_roll, sad_violin, suspense)

## What Needs to Be Built

### 1. Minecraft Parkour Background
- Download a proper Minecraft parkour video from YouTube (Creative Commons)
- Use `yt-dlp` (`pip install yt-dlp`)
- Good source: "Orbital NCG" or similar MC parkour channels
- Save as `backgrounds/parkour.mp4`
- Should be vertical (9:16) or crop to fit

### 2. Meme Pipeline Script (`meme_pipeline.py`)
The core script:

```
Step 1: Fetch 5 memes from https://meme-api.com/gimme/5
Step 2: For each meme:
  - Download the image
  - OCR the text (pytesseract or easyocr)
  - Generate TTS voiceover (edge-tts, English voice "en-US-GuyNeural")
  - Pick a random sound effect from assets/sounds/
Step 3: For each meme, render a 6-8s clip:
  - Minecraft parkour background (random segment)
  - Meme image overlaid (centered, maybe zoom)
  - TTS voiceover
  - Sound effect at end
Step 4: Concatenate all clips → final Short (30-60s)
Step 5: Output as MP4 (H264 + AAC, 1080x1920)
```

### 3. n8n Workflow (Final)
Replace basic workflow:
- Trigger: Every 6h (or manual)
- Node 1: HTTP Request → meme-api.com → get 5 memes
- Node 2: Execute Command → `python meme_pipeline.py` with meme data
- Node 3: Save output to `output/` folder

### 4. Render Server (`pc_renderer_windows.py`)
Flask server on port 8765 that accepts POST requests with meme data and renders.
Already exists — needs updating with new pipeline.

## Project Structure
```
meme-shorts-generator/
├── PLAN.md                     # This file
├── README.md
├── meme_pipeline.py            # Main pipeline script
├── pc_renderer_windows.py      # Flask render server
├── START_RENDERER.bat          # Start render server
├── SETUP_MEMES.bat             # Setup dependencies
├── backgrounds/
│   └── parkour.mp4             # MC parkour background
├── assets/
│   ├── reactions/              # Real reaction meme images (NOT emojis)
│   │   ├── speed_eyes_closed.png
│   │   ├── shocked_guy.jpg
│   │   └── ...
│   └── sounds/                 # Sound effects
│       ├── vine_boom.mp3
│       ├── laugh.mp3
│       └── ...
├── output/                     # Rendered Shorts (gitignored)
└── temp/                       # Temp files (gitignored)
```

## Constraints (Jakob's Preferences)
- **NO subtitles** — distracting
- **NO emojis** — use real reaction meme images
- **NO KI narration/moderation** — only read OCR text from meme
- **English voice** for memes (edge-tts en-US)
- **Minecraft parkour** from YouTube, not stock footage
- **3-5 memes per Short**, each ~6-8s
- **Sound effects** between memes
- **Render on PC** — VPS too slow

## Technical Notes
- n8n installed with `--ignore-scripts` → Code nodes won't work (no isolated-vm)
  - Fix: `winget install Microsoft.VisualStudio.2022.BuildTools` then reinstall n8n
- Tesseract OCR needed: `winget install UB-Mannheim.TesseractOCR`
- `pip install yt-dlp pytesseract easyocr`

## First Steps
1. Install missing: `winget install UB-Mannheim.TesseractOCR` + `pip install yt-dlp pytesseract`
2. Download MC parkour video from YouTube
3. Build `meme_pipeline.py` — start with 1 meme, then scale to 5
4. Test render locally
5. Update n8n workflow to trigger pipeline
6. Polish: transitions, timing, reaction images

## n8n API
- URL: `http://100.83.156.25:5678`
- Header: `X-N8N-API-KEY: <key>`
- Workflow ID: `Qhy8bDVbsWUZGQVY`
