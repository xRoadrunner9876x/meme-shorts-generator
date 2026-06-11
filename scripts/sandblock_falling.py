"""
Minecraft Sand Block Falling - YouTube Short (9:16, 1080x1920)
Blender 5.x | EEVEE | Foolproof

1. Script pasten → Run (▶️)
2. F12 = Einzelbild testen (Vorschau)
3. Strg+F12 = Ganze Animation rendern → MP4 landet auf dem Desktop
"""

import bpy
import math
import os
import subprocess
from mathutils import Vector

# ============================================================
# 1. SZENE LEEREN
# ============================================================
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for coll in [bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
             bpy.data.lights, bpy.data.worlds]:
    for item in coll:
        coll.remove(item)

scene = bpy.context.scene

# ============================================================
# 2. RENDER SETTINGS (EEVEE = schnell!)
# ============================================================
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.fps = 60
scene.frame_start = 1
scene.frame_end = 120  # 2 Sekunden

# Output → Desktop/blender_renders/ (PNG Einzelbilder)
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
render_dir = os.path.join(desktop, "blender_renders")
os.makedirs(render_dir, exist_ok=True)
scene.render.filepath = os.path.join(render_dir, "frame_")

# PNG Einzelbilder (sicherster Weg)
scene.render.image_settings.media_type = 'IMAGE'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'

# EEVEE Settings für bessere Qualität


# ============================================================
# 3. HELPER
# ============================================================
def make_cube(name, location, size=1.0):
    s = size / 2
    verts = [
        (-s, -s, -s), (-s, -s, s), (-s, s, -s), (-s, s, s),
        (s, -s, -s), (s, -s, s), (s, s, -s), (s, s, s),
    ]
    faces = [
        (0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
        (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3),
    ]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    scene.collection.objects.link(obj)
    return obj


def add_mat(obj, name, color, roughness=0.8):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    obj.data.materials.append(mat)


def add_rb(obj, body_type='ACTIVE', mass=1.0, friction=0.5, restitution=0.0):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.type = body_type
    obj.rigid_body.mass = mass
    obj.rigid_body.friction = friction
    obj.rigid_body.restitution = restitution


# ============================================================
# 4. OBJEKTE
# ============================================================

# --- Sandblock (fällt!) ---
sandblock = make_cube("Sandblock", (0, 0, 3.0), size=1.0)
sandblock.rotation_euler = (0.1, 0.05, 0.3)
add_mat(sandblock, "Sand", (0.84, 0.72, 0.47, 1.0), 0.85)
add_rb(sandblock, 'ACTIVE', mass=5.0, friction=0.7, restitution=0.05)
sandblock.rigid_body.linear_damping = 0.1
sandblock.rigid_body.angular_damping = 0.3

# --- Boden ---
ground = make_cube("Ground", (0, 0, -1.0), size=2.0)
ground.scale = (8, 8, 1)
add_mat(ground, "Grass", (0.35, 0.55, 0.25, 1.0), 0.9)
add_rb(ground, 'PASSIVE', friction=0.8)

# --- 2 Deko-Blöcke ---
for i, (pos, col, sz) in enumerate([
    ((-3, 2, 0), (0.45, 0.32, 0.18, 1.0), 0.6),
    ((3, -1.5, 0), (0.50, 0.50, 0.50, 1.0), 0.7),
]):
    block = make_cube(f"Deco_{i}", pos, size=sz)
    add_mat(block, f"DecoMat_{i}", col, 0.9)
    add_rb(block, 'PASSIVE', friction=0.8)

# ============================================================
# 5. KAMERA
# ============================================================
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
camera = bpy.data.objects.new("Camera", cam_data)
camera.location = (4.0, -5.0, 5.0)
direction = Vector((0, 0, 1.5)) - camera.location
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(camera)
scene.camera = camera

# ============================================================
# 6. LICHT
# ============================================================
# Key Light
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 5.0
sun_data.color = (1.0, 0.95, 0.85)
sun = bpy.data.objects.new("Sun", sun_data)
sun.location = (5, -3, 10)
sun.rotation_euler = (math.radians(40), math.radians(10), math.radians(20))
scene.collection.objects.link(sun)

# Fill Light
fill_data = bpy.data.lights.new("Fill", 'AREA')
fill_data.energy = 300
fill_data.size = 5
fill_data.color = (0.8, 0.85, 1.0)
fill = bpy.data.objects.new("Fill", fill_data)
fill.location = (-5, -3, 6)
fill.rotation_euler = (math.radians(50), 0, math.radians(-20))
scene.collection.objects.link(fill)

# ============================================================
# 7. WORLD
# ============================================================
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs['Color'].default_value = (0.78, 0.88, 0.95, 1.0)
bg.inputs['Strength'].default_value = 1.2

# ============================================================
# 8. AUTO-CONVERT: Nach dem Rendern → MP4 via ffmpeg
# ============================================================
# Handler der nach dem Rendern ffmpeg aufruft
import tempfile

def convert_to_mp4(scene):
    """Wird nach jedem Render aufgerufen. Konvertiert PNGs → MP4."""
    png_pattern = os.path.join(render_dir, "frame_")
    mp4_path = os.path.join(desktop, "minecraft_short.mp4")

    # Finde das PNG-Pattern (Blender nutzt #### für Frame-Nummern)
    cmd = [
        "ffmpeg", "-y",
        "-framerate", "60",
        "-i", f"{png_pattern}%04d.png",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        mp4_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f"MP4 ERSTELLT: {mp4_path}")
        else:
            print(f"FFmpeg Fehler: {result.stderr[:200]}")
    except FileNotFoundError:
        print("FFmpeg nicht gefunden! Installiere es: https://ffmpeg.org")
    except Exception as e:
        print(f"Fehler: {e}")


# Handler registrieren (wird nach Ctrl+F12 automatisch aufgerufen)
bpy.app.handlers.render_complete.clear()
bpy.app.handlers.render_complete.append(convert_to_mp4)


# ============================================================
# FERTIG!
# ============================================================
print("=" * 50)
print("SZENE FERTIG!")
print(f"Render-Ordner: {render_dir}")
print("")
print("F12       = Einzelbild testen")
print("Strg+F12  = Animation rendern → MP4 auf Desktop")
print("")
print(f"MP4 landet auf: {desktop}/minecraft_short.mp4")
print("=" * 50)
