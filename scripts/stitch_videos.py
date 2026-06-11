"""
VoxelSim - Stitch Script
Schneidet alle 4 Szenen zusammen zu einem fertigen Short.

Usage:
  python stitch_videos.py
  
Output: Desktop/voxelsim_renders/final_escalation.mp4
"""

import subprocess
import os

DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
RENDER_DIR = os.path.join(DESKTOP, "voxelsim_renders")

# Szenen in Reihenfolge
SCENES = ["1_block", "4_blocks", "16_blocks", "50_blocks"]

def find_video(scene_name):
    """Findet das MP4 einer Szene."""
    path = os.path.join(RENDER_DIR, scene_name, "animation.mp4")
    if os.path.exists(path):
        return path
    print(f"  WARNUNG: {path} nicht gefunden!")
    return None

def main():
    print("VoxelSim Escalation Stitcher")
    print("=" * 50)
    
    # Alle Videos finden
    videos = []
    for scene in SCENES:
        path = find_video(scene)
        if path:
            videos.append(path)
            print(f"  ✅ {scene}: {path}")
        else:
            print(f"  ❌ {scene}: nicht gefunden")
    
    if len(videos) < 2:
        print("\nMindestens 2 Videos benötigt!")
        print("Erst alle 4 Szenen rendern (SCENE_ID = 1,2,3,4)")
        return
    
    # Concat-Liste erstellen
    concat_file = os.path.join(RENDER_DIR, "concat_list.txt")
    with open(concat_file, 'w') as f:
        for v in videos:
            f.write(f"file '{v}'\n")
    
    # Output
    output = os.path.join(RENDER_DIR, "final_escalation.mp4")
    
    # FFmpeg: concat + optionaler Sound
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        output
    ]
    
    print(f"\nSchneide {len(videos)} Videos zusammen...")
    print(f"Output: {output}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            size_mb = os.path.getsize(output) / (1024 * 1024)
            print(f"\n{'='*50}")
            print(f"FERTIG! {output}")
            print(f"Größe: {size_mb:.1f} MB")
            print(f"Szenen: {len(videos)}")
            print(f"{'='*50}")
        else:
            print(f"FFmpeg Fehler: {result.stderr[:300]}")
    except FileNotFoundError:
        print("FFmpeg nicht gefunden!")
    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    main()
