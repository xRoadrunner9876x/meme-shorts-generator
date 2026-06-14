"""
🎬 Meme Shorts Generator — Alles auf dem PC
Führt alles lokal aus: Meme-Fetch, OCR, TTS, ffmpeg-Rendering.

Benötigt:
  pip install flask requests pytesseract Pillow edge-tts
  + ffmpeg im PATH
  + Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
"""

import json, os, sys, time, random, subprocess, tempfile, re, glob
from pathlib import Path
from urllib.request import Request, urlopen

# ── Config ──────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
PARKOUR_DIR = SCRIPT_DIR / "parkour"
SOUNDS_DIR = SCRIPT_DIR / "sounds"
REACTIONS_DIR = SCRIPT_DIR / "reactions"
OUTPUT_DIR = SCRIPT_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

WIDTH, HEIGHT = 720, 1280
VOICE = "en-US-AndrewMultilingualNeural"

# ── Utilities ───────────────────────────────────────────────

def get_duration(path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=10
        )
        return float(r.stdout.strip())
    except:
        return 0


def download_file(url, path):
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=15) as r:
            with open(path, "wb") as f:
                f.write(r.read())
        return os.path.exists(path) and os.path.getsize(path) > 500
    except Exception as e:
        print(f"  [!] Download failed: {e}")
        return False


def download_image(url, path):
    raw = path + ".raw"
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=15) as r:
            with open(raw, "wb") as f:
                f.write(r.read())
        r = subprocess.run(["ffmpeg", "-y", "-i", raw, "-vframes", "1", "-q:v", "2", path],
                           capture_output=True, timeout=15)
        if os.path.exists(raw):
            os.remove(raw)
        return r.returncode == 0 and os.path.getsize(path) > 1000
    except:
        if os.path.exists(raw):
            os.remove(raw)
        return False


# ── Meme Fetching ───────────────────────────────────────────

def fetch_memes(count=4):
    """Fetch memes from meme-api.com"""
    memes = []
    seen = set()
    attempts = 0
    while len(memes) < count and attempts < count * 3:
        attempts += 1
        try:
            req = Request("https://meme-api.com/gimme", headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            if data.get("nsfw") or data["url"] in seen:
                continue
            seen.add(data["url"])
            memes.append({
                "title": data["title"],
                "url": data["url"],
                "subreddit": data.get("subreddit", "memes"),
            })
        except Exception as e:
            print(f"  [!] Fetch failed: {e}")
            time.sleep(1)
    return memes


# ── OCR ─────────────────────────────────────────────────────

def ocr_meme(image_path):
    """Extract text from meme image via Tesseract OCR"""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='eng')
        text = text.strip()
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[|{}[\]<>()]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        # Filter garbage: too short, single chars, just numbers
        if len(text) < 10:
            return None
        if re.match(r'^[A-Z0-9\s]{1,5}$', text):
            return None
        return text
    except Exception as e:
        print(f"  OCR error: {e}")
        return None


# ── TTS ─────────────────────────────────────────────────────

def generate_voice(text, output_path):
    """Generate voice with edge-tts"""
    cmd = [
        "edge-tts", "--voice", VOICE, "--text", text,
        "--write-media", str(output_path), "--rate", "+15%",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        print(f"  [!] TTS failed: {r.stderr[:100]}")
        return 0
    return get_duration(output_path)


# ── Parkour ─────────────────────────────────────────────────

def get_parkour_video():
    """Find or download Minecraft parkour video"""
    # Check for existing parkour videos
    for f in PARKOUR_DIR.glob("*.mp4"):
        if f.stat().st_size > 1_000_000:  # > 1MB
            return f
    
    # Download from Orbital NCG (No Copyright Minecraft Parkour)
    print("  Downloading Minecraft parkour video...")
    PARKOUR_DIR.mkdir(exist_ok=True)
    output = PARKOUR_DIR / "minecraft_parkour.mp4"
    
    # Try yt-dlp
    try:
        r = subprocess.run([
            "yt-dlp", "-f", "bestvideo[height<=1280][ext=mp4]+bestaudio[ext=m4a]/best[height<=1280]",
            "--merge-output-format", "mp4",
            "-o", str(output),
            "https://www.youtube.com/watch?v=WTNGbkOTi68",
            "--no-playlist",
        ], capture_output=True, text=True, timeout=600)
        if r.returncode == 0 and output.exists():
            print(f"  Downloaded: {output.stat().st_size / 1e6:.0f}MB")
            return output
    except Exception as e:
        print(f"  yt-dlp failed: {e}")
    
    # Fallback: use Pexels
    print("  Trying Pexels for parkour...")
    try:
        env_path = SCRIPT_DIR.parent / ".env"
        pexels_key = ""
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if "PEXELS" in line and "=" in line:
                    pexels_key = line.split("=", 1)[1].strip()
        
        if pexels_key:
            req = Request("https://api.pexels.com/videos/search?query=minecraft+parkour&per_page=3&orientation=portrait",
                         headers={"Authorization": pexels_key})
            with urlopen(req, timeout=15) as r:
                data = json.loads(r.read())
            for v in data.get("videos", []):
                for f in v["video_files"]:
                    if f.get("height", 0) >= 1280 and f.get("width", 0) <= 720:
                        if download_file(f["link"], str(output)):
                            return output
    except:
        pass
    
    print("  [!] No parkour video available!")
    return None


# ── Rendering ───────────────────────────────────────────────

def render_meme_clip(parkour_path, meme_image, audio_path, output_path):
    """Render: parkour bg + meme overlay + voice"""
    duration = get_duration(audio_path)
    if duration < 0.5:
        return None

    parkour_dur = get_duration(parkour_path)
    max_start = max(0, parkour_dur - duration - 5)
    start = random.uniform(0, max_start) if max_start > 0 else 0
    meme_w = int(WIDTH * 0.80)

    # Two-step: trim parkour, then overlay
    tmp_trim = output_path.replace(".mp4", "_trim.mp4")
    
    # Step 1: Trim parkour (stream copy = instant)
    subprocess.run([
        "ffmpeg", "-y", "-ss", str(start), "-i", str(parkour_path),
        "-t", str(duration), "-c", "copy", tmp_trim
    ], capture_output=True, timeout=30)

    # Step 2: Overlay meme
    subprocess.run([
        "ffmpeg", "-y",
        "-i", tmp_trim, "-loop", "1", "-framerate", "1", "-i", str(meme_image),
        "-i", str(audio_path),
        "-filter_complex",
        f"[1:v]scale={meme_w}:-2[meme];[0:v][meme]overlay=(W-w)/2:(H-h)/2,format=yuv420p[out]",
        "-map", "[out]", "-map", "2:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(duration), "-pix_fmt", "yuv420p", "-shortest",
        str(output_path),
    ], capture_output=True, timeout=120)

    try:
        os.remove(tmp_trim)
    except:
        pass

    if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
        return output_path
    return None


def render_reaction(reaction_img, sound_path, output_path):
    """Render: reaction image full-screen + sound effect"""
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-framerate", "1", "-i", str(reaction_img),
        "-i", str(sound_path),
        "-vf", f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},format=yuv420p",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", "1.2", "-pix_fmt", "yuv420p", "-shortest",
        str(output_path),
    ], capture_output=True, timeout=30)

    if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
        return output_path
    return None


def concat_clips(clips, output_path):
    """Concatenate all clips into final video"""
    list_file = output_path.replace(".mp4", "_list.txt")
    with open(list_file, "w") as f:
        for p in clips:
            f.write(f"file '{p}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(output_path),
    ], capture_output=True, timeout=120)

    try:
        os.remove(list_file)
    except:
        pass

    if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
        return output_path
    return None


# ── Main Pipeline ───────────────────────────────────────────

def generate_meme_short(meme_count=4):
    ts = time.strftime("%Y%m%d_%H%M%S")
    tmp = tempfile.mkdtemp(prefix="meme_")
    print(f"\n{'='*50}")
    print(f"  🎬 Meme Short Generator")
    print(f"  Memes: {meme_count} | Tmp: {tmp}")
    print(f"{'='*50}\n")

    # Clean old output
    for old in OUTPUT_DIR.glob("meme_*.mp4"):
        old.unlink()

    # 1. Parkour video
    print("[1/6] Minecraft Parkour...")
    parkour = get_parkour_video()
    if not parkour:
        print("ERROR: Kein Parkour-Video! Erstelle 'parkour/' Ordner mit einer .mp4 Datei.")
        return None
    print(f"  ✓ {parkour.name} ({parkour.stat().st_size / 1e6:.0f}MB)")

    # 2. Fetch memes
    print("[2/6] Memes holen...")
    memes = fetch_memes(meme_count)
    if not memes:
        print("ERROR: Keine Memes gefunden")
        return None
    print(f"  ✓ {len(memes)} Memes")

    # 3. Download images
    print("[3/6] Bilder herunterladen...")
    for i, meme in enumerate(memes):
        img = os.path.join(tmp, f"meme_{i}.jpg")
        if not download_image(meme["url"], img):
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                "color=c=0x333333:s=720x720:d=1", "-frames:v", "1", img],
                capture_output=True, timeout=10)
        meme["image"] = img

    # 4. OCR + TTS
    print("[4/6] Text erkennen + Stimme generieren...")
    for i, meme in enumerate(memes):
        text = ocr_meme(meme["image"])
        if not text:
            text = meme["title"]
            if not text or text.lower() in ["me_irl", "meirl"]:
                text = "Check this out, that's so real"
        meme["text"] = text
        audio = os.path.join(tmp, f"audio_{i}.mp3")
        meme["duration"] = generate_voice(text, audio)
        meme["audio"] = audio
        print(f"  [{i+1}] {text[:50]}... ({meme['duration']:.1f}s)")

    # 5. Render clips
    print("[5/6] Video rendern...")
    reaction_imgs = [f for f in (list(REACTIONS_DIR.glob("*.jpg")) + list(REACTIONS_DIR.glob("*.png")))
                     if f.stat().st_size > 5000]
    sound_files = list(SOUNDS_DIR.glob("*.mp3"))
    clips = []

    for i, meme in enumerate(memes):
        # Meme on parkour
        clip = os.path.join(tmp, f"clip_{i}.mp4")
        print(f"  Clip {i+1}/{len(memes)}...")
        result = render_meme_clip(parkour, meme["image"], meme["audio"], clip)
        if result:
            clips.append(result)

        # Reaction transition
        if i < len(memes) - 1 and reaction_imgs and sound_files:
            trans = os.path.join(tmp, f"trans_{i}.mp4")
            reaction = random.choice(reaction_imgs)
            sound = random.choice(sound_files)
            print(f"  → {reaction.name} + {sound.name}")
            result = render_reaction(reaction, sound, trans)
            if result:
                clips.append(result)

    if not clips:
        print("ERROR: Keine Clips gerendert")
        return None

    # 6. Concatenate
    output = str(OUTPUT_DIR / f"meme_{ts}.mp4")
    print(f"[6/6] {len(clips)} Clips zusammenfügen...")
    result = concat_clips(clips, output)

    if result:
        size = os.path.getsize(result) / (1024 * 1024)
        dur = get_duration(result)
        print(f"\n{'='*50}")
        print(f"  ✅ FERTIG: {result}")
        print(f"  📁 Größe: {size:.1f}MB | Dauer: {dur:.1f}s")
        print(f"{'='*50}")
        return result
    return None


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    generate_meme_short(count)
