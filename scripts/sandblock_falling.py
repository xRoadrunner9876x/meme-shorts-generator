"""
Minecraft Sand Block Falling - YouTube Short (9:16, 1080x1920)
Blender 5.x compatible

WICHTIG: Vor dem Rendern eine .blend Datei speichern!
  File → Save As → z.B. Desktop/sandblock.blend
Dann: Render → Render Animation (Ctrl+F12)
Output liegt dann im Ordner "renders/" neben der .blend Datei.
"""

import bpy
import math
import os
from mathutils import Vector

# ============================================================
# 1. SZENE KOMPLETT LEEREN
# ============================================================
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

for block in [bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
              bpy.data.lights, bpy.data.worlds]:
    for item in block:
        block.remove(item)

scene = bpy.context.scene

# ============================================================
# 2. RENDER SETTINGS
# ============================================================
scene.render.engine = 'CYCLES'
scene.cycles.samples = 256
scene.cycles.use_denoising = True
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.fps = 60
scene.frame_start = 1
scene.frame_end = 120

# Output-Pfad: erstellt einen "renders" Ordner auf dem Desktop
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
render_dir = os.path.join(desktop, "blender_renders")
os.makedirs(render_dir, exist_ok=True)
scene.render.filepath = os.path.join(render_dir, "sandblock_")

# Video Output (Blender 5.x)
scene.render.image_settings.media_type = 'VIDEO'
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'

# GPU
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'CUDA'
    prefs.get_devices()
    for device in prefs.devices:
        device.use = True
    scene.cycles.device = 'GPU'
except Exception:
    scene.cycles.device = 'CPU'


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
    return mat


def add_rb(obj, body_type='ACTIVE', mass=1.0, friction=0.5, restitution=0.0):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.type = body_type
    obj.rigid_body.mass = mass
    obj.rigid_body.friction = friction
    obj.rigid_body.restitution = restitution
    return obj


# ============================================================
# 4. SANDBLOCK (fällt von oben)
# ============================================================
sandblock = make_cube("Sandblock", (0, 0, 3.0), size=1.0)
sandblock.rotation_euler = (0.1, 0.05, 0.3)
add_mat(sandblock, "Sand", (0.84, 0.72, 0.47, 1.0), 0.85)
add_rb(sandblock, 'ACTIVE', mass=5.0, friction=0.7, restitution=0.05)
sandblock.rigid_body.linear_damping = 0.1
sandblock.rigid_body.angular_damping = 0.3

# ============================================================
# 5. BODEN (großer Gras-Block)
# ============================================================
ground = make_cube("Ground", (0, 0, -1.0), size=2.0)
ground.scale = (8, 8, 1)
add_mat(ground, "Grass", (0.35, 0.55, 0.25, 1.0), 0.9)
add_rb(ground, 'PASSIVE', friction=0.8, restitution=0.0)

# ============================================================
# 6. EINZELNE DEKO-BLÖCKE (weniger = cleaner)
# ============================================================
deco_data = [
    ((-3, 2, 0), (0.45, 0.32, 0.18, 1.0), 0.6),    # Dirt
    ((3, -1.5, 0), (0.50, 0.50, 0.50, 1.0), 0.7),    # Stone
]
for i, (pos, col, sz) in enumerate(deco_data):
    block = make_cube(f"Deco_{i}", pos, size=sz)
    add_mat(block, f"DecoMat_{i}", col, roughness=0.9)
    add_rb(block, 'PASSIVE', friction=0.8)

# ============================================================
# 7. KAMERA (auf den Sandblock fokussiert)
# ============================================================
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
cam_data.dof.use_dof = True
cam_data.dof.aperture_fstop = 2.8

camera = bpy.data.objects.new("Camera", cam_data)
camera.location = (4.0, -5.0, 5.0)

# Kamera schaut auf den Sandblock
direction = Vector((0, 0, 1.5)) - camera.location
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

cam_data.dof.focus_object = sandblock
scene.collection.objects.link(camera)
scene.camera = camera

# ============================================================
# 8. LICHT (warm, cinematic)
# ============================================================
# Key Light (Sonne)
sun_data = bpy.data.lights.new("KeyLight", 'SUN')
sun_data.energy = 5.0
sun_data.color = (1.0, 0.95, 0.85)
sun_data.angle = math.radians(5)
sun = bpy.data.objects.new("KeyLight", sun_data)
sun.location = (5, -3, 10)
sun.rotation_euler = (math.radians(40), math.radians(10), math.radians(20))
scene.collection.objects.link(sun)

# Fill Light (Area, weich)
fill_data = bpy.data.lights.new("FillLight", 'AREA')
fill_data.energy = 300
fill_data.size = 5
fill_data.color = (0.8, 0.85, 1.0)
fill = bpy.data.objects.new("FillLight", fill_data)
fill.location = (-5, -3, 6)
fill.rotation_euler = (math.radians(50), 0, math.radians(-20))
scene.collection.objects.link(fill)

# ============================================================
# 9. WORLD (heller Himmel)
# ============================================================
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs['Color'].default_value = (0.78, 0.88, 0.95, 1.0)
bg.inputs['Strength'].default_value = 1.2

# ============================================================
# FERTIG!
# ============================================================
print("=" * 50)
print("SZENE FERTIG!")
print(f"Render-Ordner: {render_dir}")
print("1. File → Save As (irgendwo speichern)")
print("2. Ctrl+F12 → Rendert automatisch als MP4")
print("3. F12 → Einzelbild testen")
print("=" * 50)
