# Meme Shorts Generator

Automated YouTube Shorts from Reddit memes + Minecraft parkour.

## What it does
1. Fetches memes from Reddit
2. OCR reads the meme text
3. Generates TTS voiceover (edge-tts)
4. Overlays meme on Minecraft parkour background
5. Adds reaction images + sound effects
6. Renders a 30-60s YouTube Short

## Setup
```bash
# Install dependencies
pip install edge-tts flask requests yt-dlp pytesseract easyocr

# Install Tesseract OCR
winget install UB-Mannheim.TesseractOCR

# Install FFmpeg
winget install Gyan.FFmpeg
```

## Run
```bash
# Start the render server
START_RENDERER.bat

# Or run the pipeline directly
python meme_pipeline.py
```

## n8n Integration
n8n workflow triggers the pipeline every 6 hours automatically.
Access n8n: `http://localhost:5678`

## Project Structure
- `PLAN.md` — Full build plan for OpenCode/AI assistants
- `meme_pipeline.py` — Main pipeline script
- `pc_renderer_windows.py` — Flask render server
- `assets/reactions/` — Reaction meme images
- `assets/sounds/` — Sound effects
- `backgrounds/` — Minecraft parkour video
- `output/` — Rendered Shorts
