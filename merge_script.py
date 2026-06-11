"""
VoxelSim - Sound Merge Script
Liest collision_data.json und fügt Sounds an den Kollisions-Stellen ein.

Usage:
  python merge_script.py
  python merge_script.py --sound-dir ./sounds --output final.mp4

Benötigt: FFmpeg (https://ffmpeg.org/download.html)
"""

import json
import subprocess
import os
import sys
import argparse

# ============================================================
# CONFIG
# ============================================================
DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
DEFAULT_RENDER_DIR = os.path.join(DESKTOP, "voxelsim_renders")
DEFAULT_SOUND_DIR = os.path.join(DESKTOP, "voxelsim_sounds")

# Sound-Dateien die du brauchst (in voxelsim_sounds/ Ordner):
SOUND_MAP = {
    "impact": "impact.mp3",      # Haupaufprall (laut, tief)
    "bounce": "bounce.mp3",      # Kleiner Bounce (leiser, höher)
    "default": "thud.mp3",       # Fallback
}


def find_collision_data(render_dir):
    """Findet collision_data.json im Render-Ordner."""
    path = os.path.join(render_dir, "collision_data.json")
    if not os.path.exists(path):
        print(f"FEHLER: {path} nicht gefunden!")
        print("Erst Blender-Script mit Strg+F12 rendern.")
        sys.exit(1)
    return path


def load_collisions(json_path):
    """Lädt Collision-Daten aus JSON."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    print(f"Geladen: {len(data['collisions'])} Collision(s)")
    print(f"Video: {data.get('video_file', 'nicht angegeben')}")
    return data


def find_sound_file(sound_dir, sound_type):
    """Findet die passende Sound-Datei."""
    filename = SOUND_MAP.get(sound_type, SOUND_MAP["default"])
    path = os.path.join(sound_dir, filename)
    
    if os.path.exists(path):
        return path
    
    # Fallback: irgendeine MP3 im Sound-Ordner
    for f in os.listdir(sound_dir):
        if f.endswith(('.mp3', '.wav', '.ogg')):
            fallback = os.path.join(sound_dir, f)
            print(f"  Sound '{filename}' nicht gefunden, nutze '{f}'")
            return fallback
    
    return None


def build_ffmpeg_command(video_path, collisions, sound_dir, output_path):
    """Baut den FFmpeg-Befehl mit allen Sound-Overlays."""
    
    if not collisions:
        print("Keine Collisions gefunden! Video wird ohne Sound gespeichert.")
        return ["ffmpeg", "-y", "-i", video_path, "-c:v", "copy", output_path]
    
    # Base command: video input
    inputs = ["-i", video_path]
    filter_parts = []
    
    # Für jede Collision einen Sound-Input hinzufügen
    sound_count = 0
    for i, coll in enumerate(collisions):
        sound_type = coll.get("type", "impact")
        sound_file = find_sound_file(sound_dir, sound_type)
        
        if sound_file is None:
            print(f"  WARNUNG: Kein Sound für '{sound_type}' gefunden, überspringe")
            continue
        
        # Sound als Input hinzufügen
        inputs.extend(["-i", sound_file])
        sound_count += 1
        
        # Delay in Millisekunden
        delay_ms = int(coll["time_sec"] * 1000)
        
        # Volume basierend auf Impact-Force (lauter = stärkerer Aufprall)
        force = coll.get("force", 1.0)
        volume = min(1.5, max(0.3, force / 3.0))
        
        # Filter: Delay + Volume anpassen
        input_idx = sound_count  # 0 = video, 1+ = sounds
        filter_parts.append(
            f"[{input_idx}:a]adelay={delay_ms}|{delay_ms},volume={volume:.2f}[s{i}]"
        )
        
        print(f"  Sound {sound_count}: {os.path.basename(sound_file)} @ {coll['time_sec']}s (vol: {volume:.2f})")
    
    if sound_count == 0:
        print("Keine Sounds gefunden! Kopiere Video ohne Audio.")
        return ["ffmpeg", "-y", "-i", video_path, "-c:v", "copy", output_path]
    
    # Mix all sounds together
    mix_inputs = "".join(f"[s{i}]" for i in range(sound_count))
    filter_parts.append(
        f"{mix_inputs}amix=inputs={sound_count}:duration=first:normalize=0[aout]"
    )
    
    filter_complex = ";".join(filter_parts)
    
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ]
    
    return cmd


def main():
    parser = argparse.ArgumentParser(description="VoxelSim Sound Merger")
    parser.add_argument("--render-dir", default=DEFAULT_RENDER_DIR,
                        help="Ordner mit collision_data.json und animation.mp4")
    parser.add_argument("--sound-dir", default=DEFAULT_SOUND_DIR,
                        help="Ordner mit Sound-Dateien (mp3/wav)")
    parser.add_argument("--output", default=None,
                        help="Output-Dateiname (default: final_short.mp4)")
    args = parser.parse_args()
    
    # Collision Data laden
    json_path = find_collision_data(args.render_dir)
    data = load_collisions(json_path)
    
    # Video-Pfad
    video_path = data.get("video_file", os.path.join(args.render_dir, "animation.mp4"))
    if not os.path.exists(video_path):
        print(f"FEHLER: Video nicht gefunden: {video_path}")
        sys.exit(1)
    
    # Sound-Ordner checken
    if not os.path.exists(args.sound_dir):
        print(f"FEHLER: Sound-Ordner nicht gefunden: {args.sound_dir}")
        print(f"Erstelle den Ordner und lade Sounds rein:")
        print(f"  mkdir -p {args.sound_dir}")
        print(f"  # Von pixabay.com/sound-effects downloaden:")
        print(f"  # - impact.mp3 (Block-Aufprall)")
        print(f"  # - bounce.mp3 (kleiner Bounce)")
        print(f"  # - thud.mp3 (Fallback)")
        sys.exit(1)
    
    # Output-Pfad
    if args.output:
        output_path = args.output
    else:
        output_path = os.path.join(args.render_dir, "final_short.mp4")
    
    # FFmpeg Befehl bauen und ausführen
    print(f"\nErstelle finalen Short mit Sound...")
    print(f"Video: {video_path}")
    print(f"Sounds: {args.sound_dir}")
    print(f"Output: {output_path}")
    print("")
    
    cmd = build_ffmpeg_command(video_path, data["collisions"], args.sound_dir, output_path)
    
    print(f"FFmpeg Command:")
    print(f"  {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"\n{'='*50}")
            print(f"FERTIG! Finaler Short: {output_path}")
            print(f"Größe: {size_mb:.1f} MB")
            print(f"Collision-Sounds: {len(data['collisions'])}")
            print(f"{'='*50}")
        else:
            print(f"FFmpeg Fehler:\n{result.stderr[:500]}")
    except FileNotFoundError:
        print("FFmpeg nicht gefunden!")
        print("Download: https://ffmpeg.org/download.html")
    except Exception as e:
        print(f"Fehler: {e}")


if __name__ == "__main__":
    main()
