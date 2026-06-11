"""
VoxelSim - Batch Render Script
Rendert alle 4 Szenen nacheinander.

Usage:
  blender --background --python batch_render.py

Output: Desktop/voxelsim_renders/{1_block,4_blocks,16_blocks,50_blocks}/
"""

import bpy
import subprocess
import os

DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PIPELINE_SCRIPT = os.path.join(SCRIPT_DIR, "voxelsim_pipeline.py")

SCENES = [1, 2, 3, 4]
SCENE_NAMES = {1: "1_block", 2: "4_blocks", 3: "16_blocks", 4: "50_blocks"}

print("=" * 50)
print("VoxelSim Batch Render")
print("=" * 50)

for scene_id in SCENES:
    scene_name = SCENE_NAMES[scene_id]
    print(f"\n--- Rendering Scene {scene_id}: {scene_name} ---")
    
    # SCENE_ID im Script ändern
    with open(PIPELINE_SCRIPT, 'r') as f:
        content = f.read()
    
    content = content.replace(
        f"SCENE_ID = {scene_id - 1 if scene_id > 1 else 1}",
        f"SCENE_ID = {scene_id}"
    )
    # Fix: set correct SCENE_ID
    import re
    content = re.sub(r'^SCENE_ID = \d+', f'SCENE_ID = {scene_id}', content, flags=re.MULTILINE)
    
    with open(PIPELINE_SCRIPT, 'w') as f:
        f.write(content)
    
    # Blender-Szene leeren
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Script ausführen
    try:
        exec(open(PIPELINE_SCRIPT).read())
    except Exception as e:
        print(f"  Fehler in Szene {scene_id}: {e}")
        continue
    
    # Render
    print(f"  Rendering {scene_name}...")
    bpy.ops.render.render(animation=True)
    print(f"  ✅ {scene_name} fertig!")

print("\n" + "=" * 50)
print("Alle 4 Szenen gerendert!")
print(f"Output: {DESKTOP}/voxelsim_renders/")
print("\nJetzt: python stitch_videos.py")
print("=" * 50)
