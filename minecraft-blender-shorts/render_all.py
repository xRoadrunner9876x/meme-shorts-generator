"""
VoxelSim - Rendert alles: Preview + alle 4 Szenen + Zusammenführung.

Usage:
  python render_all.py              # Nur Preview (1 Frame)
  python render_all.py --full       # Alle 4 Szenen rendern + zusammenfügen
"""

import subprocess
import re
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PIPELINE = os.path.join(SCRIPT_DIR, "voxelsim_pipeline.py")
DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
RENDER_DIR = os.path.join(DESKTOP, "voxelsim_renders")

BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"

SCENES = {1: "1_block", 2: "4_blocks", 3: "16_blocks", 4: "50_blocks"}


def find_blender():
    if os.path.exists(BLENDER):
        return BLENDER
    print(f"Blender nicht gefunden: {BLENDER}")
    print("Trage deinen Pfad oben in die BLENDER Variable ein.")
    sys.exit(1)


def render_preview(blender):
    print("=== Preview: 1 Frame ===\n")
    preview_script = os.path.join(SCRIPT_DIR, "preview.py")
    subprocess.run([blender, "--background", "--python", preview_script])
    preview_img = os.path.join(RENDER_DIR, "preview", "preview.png")
    if os.path.exists(preview_img):
        print(f"\nPreview: {preview_img}")
        if sys.platform == "win32":
            os.startfile(preview_img)


def render_scene(blender, scene_id):
    scene_name = SCENES[scene_id]
    print(f"\n=== Szene {scene_id}: {scene_name} ===\n")

    with open(PIPELINE, "r") as f:
        code = f.read()

    code = re.sub(r"^SCENE_ID = \d+", f"SCENE_ID = {scene_id}", code, flags=re.MULTILINE)

    temp = os.path.join(SCRIPT_DIR, "_temp.py")
    with open(temp, "w") as f:
        f.write(code)

    try:
        result = subprocess.run([blender, "--background", "--python", temp],
                                timeout=600, capture_output=True, text=True)
        for line in result.stdout.split("\n"):
            if any(k in line for k in ["IMPACT", "collision", "MP4", "Error", "FERTIG"]):
                print(f"  {line.strip()}")
        if result.returncode != 0:
            print(f"  WARNUNG: return code {result.returncode}")
            for line in result.stderr.split("\n")[-3:]:
                if line.strip():
                    print(f"  {line.strip()}")
    finally:
        if os.path.exists(temp):
            os.remove(temp)

    mp4 = os.path.join(RENDER_DIR, scene_name, "animation.mp4")
    return mp4 if os.path.exists(mp4) else None


def stitch(videos):
    print(f"\n=== Zusammenfügen ({len(videos)} Videos) ===\n")

    concat = os.path.join(RENDER_DIR, "concat.txt")
    with open(concat, "w") as f:
        for v in videos:
            f.write(f"file '{v}'\n")

    output = os.path.join(RENDER_DIR, "final_short.mp4")
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat, "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "18", output
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if os.path.exists(concat):
        os.remove(concat)

    if result.returncode == 0:
        size_mb = os.path.getsize(output) / (1024 * 1024)
        print(f"FERTIG: {output} ({size_mb:.1f} MB)")
    else:
        print(f"FFmpeg Fehler: {result.stderr[:300]}")


def main():
    blender = find_blender()

    if "--full" not in sys.argv:
        render_preview(blender)
        print("\nFür alle 4 Szenen: python render_all.py --full")
        return

    videos = []
    for scene_id in SCENES:
        mp4 = render_scene(blender, scene_id)
        if mp4:
            videos.append(mp4)
            print(f"  OK: {mp4}")

    print(f"\n{len(videos)}/4 Szenen fertig")

    if len(videos) >= 2:
        stitch(videos)


if __name__ == "__main__":
    main()
