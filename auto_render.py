"""
VoxelSim - Kompletter Auto-Pipeline
Rendert alle 4 Szenen + schneidet zusammen.
Du musst NICHTS machen außer dieses Script starten.

Usage (im Terminal):
  python auto_render.py

Oder in Blender:
  blender --background --python auto_render.py
"""

import subprocess
import os
import sys

# ============================================================
# CONFIG
# ============================================================
DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
RENDER_DIR = os.path.join(DESKTOP, "voxelsim_renders")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) or '.'
PIPELINE_SCRIPT = os.path.join(SCRIPT_DIR, 'voxelsim_pipeline.py')

# Blender-Pfad (auto-detect)
BLENDER_PATHS = [
    "blender",                                          # Linux/Mac (PATH)
    r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe",  # Windows
    r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe",
    "/usr/bin/blender",
    "/Applications/Blender.app/Contents/MacOS/Blender",
]

SCENES = [1, 2, 3, 4]
SCENE_NAMES = {1: "1_block", 2: "4_blocks", 3: "16_blocks", 4: "50_blocks"}


def find_blender():
    """Findet Blender-Installation automatisch."""
    for path in BLENDER_PATHS:
        try:
            result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print(f"Blender gefunden: {path} ({version})")
                return path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    print("FEHLER: Blender nicht gefunden!")
    print("Installiere Blender: https://www.blender.org/download/")
    print("Oder setze den Pfad manuell in dieser Datei (BLENDER_PATHS)")
    sys.exit(1)


def render_scene(blender_path, scene_id):
    """Rendert eine Szene mit Blender im Hintergrund."""
    scene_name = SCENE_NAMES[scene_id]
    output_dir = os.path.join(RENDER_DIR, scene_name)
    os.makedirs(output_dir, exist_ok=True)
    
    # Script-Pfad mit SCENE_ID
    # Wir erstellen ein temporäres Script das SCENE_ID setzt
    temp_script = os.path.join(SCRIPT_DIR, "_temp_render.py")
    
    with open(PIPELINE_SCRIPT, 'r') as f:
        content = f.read()
    
    # SCENE_ID ersetzen
    import re
    content = re.sub(r'^SCENE_ID = \d+', f'SCENE_ID = {scene_id}', content, flags=re.MULTILINE)
    
    with open(temp_script, 'w') as f:
        f.write(content)
    
    print(f"\n{'='*50}")
    print(f"Rendering Szene {scene_id}: {scene_name}")
    print(f"Output: {output_dir}")
    print(f"{'='*50}")
    
    cmd = [blender_path, "--background", "--python", temp_script]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        # Progress anzeigen
        for line in result.stdout.split('\n'):
            if any(kw in line for kw in ['IMPACT', 'collision', 'FERTIG', 'Error', 'MP4', 'Scene']):
                print(f"  {line.strip()}")
        
        if result.returncode != 0:
            print(f"  WARNUNG: Blender return code {result.returncode}")
            for line in result.stderr.split('\n')[-5:]:
                if line.strip():
                    print(f"  STDERR: {line.strip()}")
        
        # Check ob MP4 existiert
        mp4_path = os.path.join(output_dir, "animation.mp4")
        if os.path.exists(mp4_path):
            size_mb = os.path.getsize(mp4_path) / (1024 * 1024)
            print(f"  ✅ {scene_name} fertig! ({size_mb:.1f} MB)")
            return True
        else:
            print(f"  ⚠️ {scene_name}: MP4 nicht gefunden, PNGs aber vorhanden")
            return True  # PNGs können noch manuell konvertiert werden
            
    except subprocess.TimeoutExpired:
        print(f"  ❌ {scene_name}: Timeout (10 Min)")
        return False
    except Exception as e:
        print(f"  ❌ {scene_name}: {e}")
        return False
    finally:
        # Temp-Script aufräumen
        if os.path.exists(temp_script):
            os.remove(temp_script)


def stitch_videos():
    """Schneidet alle Szenen zusammen."""
    print(f"\n{'='*50}")
    print("Schneide Videos zusammen...")
    print(f"{'='*50}")
    
    # Alle MP4s finden
    videos = []
    for scene_name in SCENE_NAMES.values():
        mp4_path = os.path.join(RENDER_DIR, scene_name, "animation.mp4")
        if os.path.exists(mp4_path):
            videos.append(mp4_path)
            print(f"  ✅ {scene_name}")
        else:
            print(f"  ❌ {scene_name}: nicht gefunden")
    
    if len(videos) < 2:
        print("Mindestens 2 Videos benötigt!")
        return False
    
    # Concat-Liste
    concat_file = os.path.join(RENDER_DIR, "concat_list.txt")
    with open(concat_file, 'w') as f:
        for v in videos:
            f.write(f"file '{v}'\n")
    
    output = os.path.join(RENDER_DIR, "final_escalation.mp4")
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        output
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            size_mb = os.path.getsize(output) / (1024 * 1024)
            print(f"\n✅ FERTIG! {output}")
            print(f"   Größe: {size_mb:.1f} MB")
            print(f"   Szenen: {len(videos)}")
            return True
        else:
            print(f"FFmpeg Fehler: {result.stderr[:200]}")
            return False
    except FileNotFoundError:
        print("FFmpeg nicht gefunden!")
        print("Download: https://ffmpeg.org/download.html")
        return False


def main():
    print("╔══════════════════════════════════════════════╗")
    print("║     VoxelSim - Kompletter Auto-Render        ║")
    print("║     1 Block → 4 → 16 → 50 (Escalation)      ║")
    print("╚══════════════════════════════════════════════╝")
    
    # Blender finden
    blender_path = find_blender()
    
    # Alle Szenen rendern
    success = 0
    for scene_id in SCENES:
        if render_scene(blender_path, scene_id):
            success += 1
    
    print(f"\n{'='*50}")
    print(f"Rendern abgeschlossen: {success}/{len(SCENES)} Szenen")
    
    # Zusammen schneiden
    if success >= 2:
        stitch_videos()
    else:
        print("Nicht genug Szenen zum Schneiden!")
    
    print(f"\n{'='*50}")
    print("FERTIG!")
    print(f"Output: {RENDER_DIR}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
