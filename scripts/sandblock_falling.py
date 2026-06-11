"""
Minecraft Sand Block Falling - YouTube Short (9:16, 1080x1920)
Blender 5.x compatible - KEINE bpy.ops mehr nötig

Öffne Blender → Scripting Tab → New → Paste → Run Script (▶️)
Dann: Render → Render Animation (Ctrl+F12)
"""

import bpy
import math
from mathutils import Vector, Euler

# ============================================================
# 1. SZENE KOMPLETT LEEREN
# ============================================================
# Alle Objekte löschen
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Alle Daten aufräumen
for block in [bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.worlds]:
    for item in block:
        block.remove(item)

scene = bpy.context.scene

# ============================================================
# 2. RENDER SETTINGS
# ============================================================
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.fps = 60
scene.frame_start = 1
scene.frame_end = 120
scene.render.filepath = "//renders/sandblock_"

# Video Output (Blender 5.x: media_type zuerst!)
scene.render.image_settings.media_type = 'VIDEO'
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'

# GPU aktivieren
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
# 3. HELPER: Objekt erstellen ohne bpy.ops
# ============================================================
def make_mesh_obj(name, location, verts, faces):
    """Erstellt ein Mesh-Objekt direkt, ohne bpy.ops."""
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    scene.collection.objects.link(obj)
    return obj



def add_material(obj, name, color, roughness=0.8):
    """Fügt ein Material zu einem Objekt hinzu."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    obj.data.materials.append(mat)
    return mat


def add_rigidbody(obj, body_type='ACTIVE', mass=1.0, friction=0.5, restitution=0.0):
    """Fügt Rigid Body hinzu."""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.type = body_type
    obj.rigid_body.mass = mass
    obj.rigid_body.friction = friction
    obj.rigid_body.restitution = restitution
    return obj


def make_cube(name, location, size=1.0):
    """Erstellt einen Würfel direkt."""
    s = size / 2
    verts = [
        (-s, -s, -s), (-s, -s, s), (-s, s, -s), (-s, s, s),
        (s, -s, -s), (s, -s, s), (s, s, -s), (s, s, s),
    ]
    faces = [
        (0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
        (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3),
    ]
    return make_mesh_obj(name, location, verts, faces)


# Farben
SAND_COLOR = (0.84, 0.72, 0.47, 1.0)
GROUND_COLOR = (0.35, 0.55, 0.25, 1.0)
BG_COLOR = (0.78, 0.88, 0.95, 1.0)

# ============================================================
# 4. SANDBLOCK
# ============================================================
sandblock = make_cube("Sandblock", (0, 0, 3.0), size=1.0)
sandblock.rotation_euler = (0.1, 0.05, 0.3)
add_material(sandblock, "Sand", SAND_COLOR, roughness=0.85)
add_rigidbody(sandblock, 'ACTIVE', mass=5.0, friction=0.7, restitution=0.05)
sandblock.rigid_body.linear_damping = 0.1
sandblock.rigid_body.angular_damping = 0.3

# ============================================================
# 5. BODEN
# ============================================================
ground = make_cube("Ground", (0, 0, -0.5), size=2.0)
ground.scale = (5, 5, 0.5)
add_material(ground, "Grass", GROUND_COLOR, roughness=0.9)
add_rigidbody(ground, 'PASSIVE', friction=0.8, restitution=0.0)

# ============================================================
# 6. DEKO-BLÖCKE
# ============================================================
deco_data = [
    ((-2.5, 1.0, 0.0), (0.45, 0.32, 0.18, 1.0)),
    ((2.0, -1.5, 0.0), (0.50, 0.50, 0.50, 1.0)),
    ((-1.5, -2.0, 0.0), (0.30, 0.55, 0.28, 1.0)),
    ((3.0, 0.5, 0.0), (0.55, 0.40, 0.22, 1.0)),
]

for i, (pos, col) in enumerate(deco_data):
    block = make_cube(f"DecoBlock_{i}", pos, size=0.8)
    block.rotation_euler = (0, 0, math.radians(15 * i))
    add_material(block, f"Deco_{i}", col, roughness=0.9)
    add_rigidbody(block, 'PASSIVE', friction=0.8)

# ============================================================
# 7. KAMERA (9:16 Portrait)
# ============================================================
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35
cam_data.dof.use_dof = True
cam_data.dof.aperture_fstop = 2.8
camera = bpy.data.objects.new("Camera", cam_data)
camera.location = (3.5, -4.0, 4.5)
direction = Vector((0, 0, 1.5)) - camera.location
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam_data.dof.focus_object = sandblock
scene.collection.objects.link(camera)
scene.camera = camera

# ============================================================
# 8. LICHT (3-Punkt)
# ============================================================
# Key Light
sun_data = bpy.data.lights.new("KeyLight", 'SUN')
sun_data.energy = 4.0
sun_data.color = (1.0, 0.95, 0.85)
sun = bpy.data.objects.new("KeyLight", sun_data)
sun.location = (5, -3, 8)
sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(30))
scene.collection.objects.link(sun)

# Fill Light
fill_data = bpy.data.lights.new("FillLight", 'AREA')
fill_data.energy = 200
fill_data.size = 3
fill_data.color = (0.8, 0.85, 1.0)
fill = bpy.data.objects.new("FillLight", fill_data)
fill.location = (-4, -2, 5)
fill.rotation_euler = (math.radians(60), 0, math.radians(-30))
scene.collection.objects.link(fill)

# Rim Light
rim_data = bpy.data.lights.new("RimLight", 'AREA')
rim_data.energy = 150
rim_data.size = 2
rim_data.color = (1.0, 0.9, 0.7)
rim = bpy.data.objects.new("RimLight", rim_data)
rim.location = (0, 5, 3)
rim.rotation_euler = (math.radians(-20), math.radians(160), 0)
scene.collection.objects.link(rim)

# ============================================================
# 9. WORLD / BACKGROUND
# ============================================================
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs['Color'].default_value = BG_COLOR
bg.inputs['Strength'].default_value = 1.0

# ============================================================
# FERTIG! Ctrl+F12 drücken zum Rendern.
# ============================================================
print("=" * 50)
print("SZENE FERTIG!")
print("Ctrl+F12 druecken zum Rendern.")
print("Output: renders/sandblock_####.mp4")
print("Format: 1080x1920 (9:16), 60fps, 2 Sekunden")
print("=" * 50)
