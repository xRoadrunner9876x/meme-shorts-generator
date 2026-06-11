"""
VoxelSim - Preview: Rendert 1 Frame und öffnet es.
Einfach starten um zu schauen wie's aussieht.

Usage:
  blender --background --python preview.py
  # Oder:
  python preview.py
"""

import bpy
import os
import subprocess
import sys
import re

DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PIPELINE_SCRIPT = os.path.join(SCRIPT_DIR, "voxelsim_pipeline.py")
PREVIEW_FILE = os.path.join(DESKTOP, "voxelsim_preview.png")

# Blender finden
BLENDER_PATHS = [
    "blender",
    r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe",
]

def find_blender():
    for path in BLENDER_PATHS:
        try:
            result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return path
        except:
            continue
    return "blender"

# Scene laden (nutzt SCENE_ID=1 als Standard)
with open(PIPELINE_SCRIPT, 'r') as f:
    content = f.read()

# Temporäres Script mit Single-Frame Render
preview_script = os.path.join(SCRIPT_DIR, "_preview_temp.py")

# Pipeline-Code laden, aber nur 1 Frame rendern
modified = re.sub(r'^SCENE_ID = \d+', 'SCENE_ID = 1', content, flags=re.MULTILINE)
modified = modified.replace('TOTAL_FRAMES = FPS * DURATION_SEC', 'TOTAL_FRAMES = 70')  # Frame 70 = nach Impact
modified = modified.replace("scene.render.filepath = os.path.join(OUTPUT_DIR, \"frame_\")", 
                           f"scene.render.filepath = r\"{PREVIEW_FILE[:-4]}\"")
modified = modified.replace("scene.render.image_settings.file_format = 'PNG'", 
                           "scene.render.image_settings.file_format = 'PNG'")
# Render single frame instead of animation
modified = modified + "\n\n# PREVIEW: Render frame 70 (nach Impact)\nscene.frame_set(70)\n"

with open(preview_script, 'w') as f:
    f.write(modified)

# Render
print("Rendering Preview (1 Frame)...")
blender = find_blender()
cmd = [blender, "--background", "--python", preview_script]

try:
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    # Output anzeigen
    for line in result.stdout.split('\n'):
        if any(kw in line for kw in ['IMPACT', 'collision', 'FERTIG', 'Error', 'Scene']):
            print(f"  {line.strip()}")
    
    # Preview öffnen
    if os.path.exists(PREVIEW_FILE):
        print(f"\nPreview gespeichert: {PREVIEW_FILE}")
        
        # Öffnen (plattformabhängig)
        if sys.platform == 'win32':
            os.startfile(PREVIEW_FILE)
        elif sys.platform == 'darwin':
            subprocess.run(['open', PREVIEW_FILE])
        else:
            subprocess.run(['xdg-open', PREVIEW_FILE])
    else:
        # Manchmal fügt Blender .png hinzu
        alt = PREVIEW_FILE + ".png"
        if os.path.exists(alt):
            os.rename(alt, PREVIEW_FILE)
            print(f"\nPreview: {PREVIEW_FILE}")
        else:
            print("\nPreview-Datei nicht gefunden!")
            print("Versuche manuell: blender --background --python voxelsim_pipeline.py")
            
except Exception as e:
    print(f"Fehler: {e}")
finally:
    if os.path.exists(preview_script):
        os.remove(preview_script)
