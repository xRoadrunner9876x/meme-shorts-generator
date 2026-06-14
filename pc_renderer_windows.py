"""
PC Render Server für YouTube Shorts
Starten auf dem Windows-PC, VPS schickt Daten über Tailscale.

Benötigt: Python 3 + pip install flask ffmpeg-python
FFmpeg muss im PATH sein (https://www.gyan.dev/ffmpeg/builds/)
"""
import os, sys, json, subprocess, tempfile, random
from pathlib import Path
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)
WIDTH, HEIGHT = 720, 1280

def get_duration(path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=10
        )
        return float(r.stdout.strip())
    except:
        return 0

@app.route("/render", methods=["POST"])
def render():
    """
    Expects multipart/form-data with:
    - audio: MP3 file (voice from edge-tts)
    - meme_image: JPG/PNG meme image  
    - parkour_video: MP4 parkour background (pre-scaled)
    - reaction_image: JPG/PNG reaction meme
    - reaction_sound: MP3 sound effect
    """
    tmp = tempfile.mkdtemp(prefix="meme_render_")
    
    try:
        # Save uploaded files
        audio_path = os.path.join(tmp, "audio.mp3")
        meme_path = os.path.join(tmp, "meme.jpg")
        parkour_path = os.path.join(tmp, "parkour.mp4")
        reaction_img_path = os.path.join(tmp, "reaction.jpg")
        reaction_snd_path = os.path.join(tmp, "reaction.mp3")
        
        request.files["audio"].save(audio_path)
        request.files["meme_image"].save(meme_path)
        request.files["parkour_video"].save(parkour_path)
        request.files["reaction_image"].save(reaction_img_path)
        request.files["reaction_sound"].save(reaction_snd_path)
        
        duration = get_duration(audio_path)
        parkour_dur = get_duration(parkour_path)
        max_start = max(0, parkour_dur - duration - 2)
        start_offset = random.uniform(0, max_start) if max_start > 0 else 0
        meme_w = int(WIDTH * 0.80)
        
        # Step 1: Trim parkour (stream copy, fast)
        trim_path = os.path.join(tmp, "trim.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-ss", str(start_offset), "-i", parkour_path,
            "-t", str(duration), "-c", "copy", trim_path
        ], capture_output=True, timeout=30)
        
        # Step 2: Overlay meme on parkour
        clip_path = os.path.join(tmp, "clip.mp4")
        subprocess.run([
            "ffmpeg", "-y",
            "-i", trim_path, "-loop", "1", "-framerate", "1", "-i", meme_path,
            "-i", audio_path,
            "-filter_complex",
            f"[1:v]scale={meme_w}:-2[meme];[0:v][meme]overlay=(W-w)/2:(H-h)/2,format=yuv420p[out]",
            "-map", "[out]", "-map", "2:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-t", str(duration), "-pix_fmt", "yuv420p", "-shortest",
            clip_path,
        ], capture_output=True, timeout=120)
        
        # Step 3: Reaction transition
        trans_path = os.path.join(tmp, "trans.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-framerate", "1", "-i", reaction_img_path,
            "-i", reaction_snd_path,
            "-vf", f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},format=yuv420p",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-t", "1.2", "-pix_fmt", "yuv420p", "-shortest",
            trans_path,
        ], capture_output=True, timeout=30)
        
        # Return rendered clip + transition
        return send_file(clip_path, mimetype="video/mp4", as_attachment=True, download_name="clip.mp4")
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    # Check ffmpeg
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return jsonify({"status": "ok", "ffmpeg": True})
    except:
        return jsonify({"status": "ok", "ffmpeg": False})

if __name__ == "__main__":
    print("=" * 50)
    print("  Meme Render Server gestartet!")
    print(f"  Port: 8765")
    print(f"  Tailscale: http://100.83.156.25:8765")
    print("=" * 50)
    app.run(host="0.0.0.0", port=8765, debug=False)
