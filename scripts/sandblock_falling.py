"""
Minecraft Sand Block Falling - YouTube Short (9:16, 1080x1920)
Blender 5.x compatible

Öffne Blender → Scripting Tab → New → Paste → Run Script (▶️)
Dann: Render → Render Animation (Ctrl+F12)
"""

import bpy
import math
from mathutils import Vector

# ============================================================
# 1. SZENE LEEREN
# ============================================================
bpy.ops.wm.read_factory_settings(use_empty=True)
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

# GPU aktivieren (safe - kein Fehler wenn keine GPU)
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'CUDA'
    prefs.get_devices()
    for device in prefs.devices:
        device.use = True
    scene.cycles.device = 'GPU'
    print("GPU (CUDA) aktiviert")
except Exception:
    scene.cycles.device = 'CPU'
    print("Keine GPU gefunden, nutze CPU")

# ============================================================
# 3. MATERIAL HELPER
# ============================================================
def make_material(name, color, roughness=0.8):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    return mat

# Farben
SAND_COLOR = (0.84, 0.72, 0.47, 1.0)
GROUND_COLOR = (0.35, 0.55, 0.25, 1.0)
BG_COLOR = (0.78, 0.88, 0.95, 1.0)

# ============================================================
# 4. SANDBLOCK
# ============================================================
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 3.0))
sandblock = bpy.context.selected_objects[-1]
sandblock.name = "Sandblock"

# Bevel
bevel = sandblock.modifiers.new(name="Bevel", type='BEVEL')
bevel.width = 0.02
bevel.segments = 2

# Material
mat_sand = make_material("Sand", SAND_COLOR, roughness=0.85)
sandblock.data.materials.append(mat_sand)

# Rigid Body (aktiv - fällt!)
bpy.ops.rigidbody.object_add()
sandblock.rigid_body.type = 'ACTIVE'
sandblock.rigid_body.mass = 5.0
sandblock.rigid_body.friction = 0.7
sandblock.rigid_body.restitution = 0.05
sandblock.rigid_body.linear_damping = 0.1
sandblock.rigid_body.angular_damping = 0.3
sandblock.rotation_euler = (0.1, 0.05, 0.3)

# ============================================================
# 5. BODEN
# ============================================================
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, -0.5))
ground = bpy.context.selected_objects[-1]
ground.name = "Ground"
ground.scale = (5, 5, 0.5)

mat_grass = make_material("Grass", GROUND_COLOR, roughness=0.9)
ground.data.materials.append(mat_grass)

bpy.ops.rigidbody.object_add()
ground.rigid_body.type = 'PASSIVE'
ground.rigid_body.friction = 0.8
ground.rigid_body.restitution = 0.0

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
    bpy.ops.mesh.primitive_cube_add(size=0.8, location=pos)
    block = bpy.context.selected_objects[-1]
    block.name = f"DecoBlock_{i}"
    block.rotation_euler = (0, 0, math.radians(15 * i))
    mat = make_material(f"Deco_{i}", col, roughness=0.9)
    block.data.materials.append(mat)
    bpy.ops.rigidbody.object_add()
    block.rigid_body.type = 'PASSIVE'
    block.rigid_body.friction = 0.8

# ============================================================
# 7. KAMERA (9:16 Portrait)
# ============================================================
bpy.ops.object.camera_add(location=(3.5, -4.0, 4.5))
camera = bpy.context.selected_objects[-1]
camera.name = "Camera"

direction = Vector((0, 0, 1.5)) - camera.location
rot_quat = direction.to_track_quat('-Z', 'Y')
camera.rotation_euler = rot_quat.to_euler()

camera.data.lens = 35
camera.data.dof.use_dof = True
camera.data.dof.focus_object = sandblock
camera.data.dof.aperture_fstop = 2.8

scene.camera = camera

# ============================================================
# 8. LICHT (3-Punkt)
# ============================================================
# Key Light
bpy.ops.object.light_add(type='SUN', location=(5, -3, 8))
sun = bpy.context.selected_objects[-1]
sun.name = "KeyLight"
sun.data.energy = 4.0
sun.data.color = (1.0, 0.95, 0.85)
sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(30))

# Fill Light
bpy.ops.object.light_add(type='AREA', location=(-4, -2, 5))
fill = bpy.context.selected_objects[-1]
fill.name = "FillLight"
fill.data.energy = 200
fill.data.size = 3
fill.data.color = (0.8, 0.85, 1.0)
fill.rotation_euler = (math.radians(60), 0, math.radians(-30))

# Rim Light
bpy.ops.object.light_add(type='AREA', location=(0, 5, 3))
rim = bpy.context.selected_objects[-1]
rim.name = "RimLight"
rim.data.energy = 150
rim.data.size = 2
rim.data.color = (1.0, 0.9, 0.7)
rim.rotation_euler = (math.radians(-20), math.radians(160), 0)

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
# Output: renders/sandblock_####.mp4
# ============================================================
print("=" * 50)
print("SZENE FERTIG!")
print("Ctrl+F12 druecken zum Rendern.")
print("Output: renders/sandblock_####.mp4")
print("Format: 1080x1920 (9:16), 60fps, 2 Sekunden")
print("=" * 50)
