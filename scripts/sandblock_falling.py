"""
Minecraft Sand Block Falling - YouTube Short (9:16, 1080x1920)
Öffne Blender → Scripting Tab → New → Paste → Run Script
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
# 2. RENDER SETTINGS (Cycles, GPU, 9:16 für Shorts)
# ============================================================
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
scene.cycles.samples = 128          # genug für sauber, nicht zu langsam
scene.cycles.use_denoising = True
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.fps = 60
scene.frame_start = 1
scene.frame_end = 120                # 2 Sekunden bei 60fps
scene.render.filepath = "//renders/sandblock_"
scene.render.image_settings.file_format = 'FFMPEG_VIDEO'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'

# GPU aktivieren (Cycles Preferences)
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'CUDA'  # Für NVIDIA
prefs.get_devices()
for device in prefs.devices:
    device.use = True

# ============================================================
# 3. FARBPALETTE (Minecraft-Sand)
# ============================================================
# Sand-Color: typisches Minecraft Sand
SAND_COLOR = (0.84, 0.72, 0.47, 1.0)       # #D7B878
SAND_DARK = (0.68, 0.56, 0.32, 1.0)        # Schatten-Seite
GROUND_COLOR = (0.35, 0.55, 0.25, 1.0)     # Gras-Grün
GROUND_DARK = (0.20, 0.35, 0.12, 1.0)      # Erd-Braun
SKY_COLOR = (0.53, 0.81, 0.92, 1.0)        # Himmelblau
BG_COLOR = (0.78, 0.88, 0.95, 1.0)         # Heller Hintergrund


def make_material(name, color, roughness=0.8):
    """Erstellt ein einfaches Principled BSDF Material."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    return mat


# ============================================================
# 4. SANDBLOCK (Minecraft-Style Würfel mit Subdivision)
# ============================================================
# Hauptblock
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 3.0))
sandblock = bpy.context.active_object
sandblock.name = "Sandblock"
sandblock.scale = (1, 1, 1)

# Bevel für weiche Kanten (Minecraft-Blöcke sind nicht perfekt scharf)
bevel = sandblock.modifiers.new(name="Bevel", type='BEVEL')
bevel.width = 0.02
bevel.segments = 2

# Material
mat_sand = make_material("Sand", SAND_COLOR, roughness=0.85)
sandblock.data.materials.append(mat_sand)

# Rigid Body (fällt!)
bpy.ops.rigidbody.object_add()
sandblock.rigid_body.type = 'ACTIVE'
sandblock.rigid_body.mass = 5.0
sandblock.rigid_body.friction = 0.7
sandblock.rigid_body.restitution = 0.05      # kaum Bounce (Sand)
sandblock.rigid_body.linear_damping = 0.1
sandblock.rigid_body.angular_damping = 0.3
sandblock.rotation_euler = (0.1, 0.05, 0.3)  # Leicht schräg fallen lassen

# ============================================================
# 5. BODEN (Gras-Block, Minecraft-Style)
# ============================================================
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, -0.5))
ground = bpy.context.active_object
ground.name = "Ground"
ground.scale = (5, 5, 0.5)

mat_grass = make_material("Grass", GROUND_COLOR, roughness=0.9)
ground.data.materials.append(mat_grass)

# Rigid Body (statisch - Boden bewegt sich nicht)
bpy.ops.rigidbody.object_add()
ground.rigid_body.type = 'PASSIVE'
ground.rigid_body.friction = 0.8
ground.rigid_body.restitution = 0.0

# ============================================================
# 6. EINIGE DEKOR-BLÖCKE (für visuelles Interesse)
# ============================================================
deco_positions = [
    (-2.5, 1.0, 0.0),
    (2.0, -1.5, 0.0),
    (-1.5, -2.0, 0.0),
    (3.0, 0.5, 0.0),
]

deco_colors = [
    (0.45, 0.32, 0.18, 1.0),   # Dirt
    (0.50, 0.50, 0.50, 1.0),   # Stone
    (0.30, 0.55, 0.28, 1.0),   # Gras
    (0.55, 0.40, 0.22, 1.0),   # Dirt dunkel
]

for i, (pos, col) in enumerate(zip(deco_positions, deco_colors)):
    bpy.ops.mesh.primitive_cube_add(size=0.8, location=pos)
    block = bpy.context.active_object
    block.name = f"DecoBlock_{i}"
    block.rotation_euler = (0, 0, math.radians(15 * i))
    mat = make_material(f"Deco_{i}", col, roughness=0.9)
    block.data.materials.append(mat)
    bpy.ops.rigidbody.object_add()
    block.rigid_body.type = 'PASSIVE'
    block.rigid_body.friction = 0.8

# ============================================================
# 7. KAMERA (9:16 Portrait-Format, cinematic Winkel)
# ============================================================
bpy.ops.object.camera_add(location=(3.5, -4.0, 4.5))
camera = bpy.context.active_object
camera.name = "Camera"

# Auf den Fallpunkt schauen
direction = Vector((0, 0, 1.5)) - camera.location
rot_quat = direction.to_track_quat('-Z', 'Y')
camera.rotation_euler = rot_quat.to_euler()

camera.data.lens = 35              # Leichtes Weitwinkel
camera.data.dof.use_dof = True
camera.data.dof.focus_object = sandblock
camera.data.dof.aperture_fstop = 2.8  # Schöner Bokeh

scene.camera = camera

# ============================================================
# 8. LICHT (3-Punkt-Beleuchtung)
# ============================================================
# Key Light (Sonne)
bpy.ops.object.light_add(type='SUN', location=(5, -3, 8))
sun = bpy.context.active_object
sun.name = "KeyLight"
sun.data.energy = 4.0
sun.data.color = (1.0, 0.95, 0.85)       # Warmes Licht
sun.rotation_euler = (math.radians(45), math.radians(15), math.radians(30))

# Fill Light (Area)
bpy.ops.object.light_add(type='AREA', location=(-4, -2, 5))
fill = bpy.context.active_object
fill.name = "FillLight"
fill.data.energy = 200
fill.data.size = 3
fill.data.color = (0.8, 0.85, 1.0)       # Kühleres Fülllicht
fill.rotation_euler = (math.radians(60), 0, math.radians(-30))

# Rim Light (Backlight)
bpy.ops.object.light_add(type='AREA', location=(0, 5, 3))
rim = bpy.context.active_object
rim.name = "RimLight"
rim.data.energy = 150
rim.data.size = 2
rim.data.color = (1.0, 0.9, 0.7)         # Warm
rim.rotation_euler = (math.radians(-20), math.radians(160), 0)

# ============================================================
# 9. WELT / BACKGROUND
# ============================================================
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs['Color'].default_value = BG_COLOR
bg.inputs['Strength'].default_value = 1.0

# ============================================================
# 10. PHYSICS BAKEN (wichtig! sonst fällt der Block nicht)
# ============================================================
# Select the sandblock for baking
bpy.ops.object.select_all(action='DESELECT')
sandblock.select_set(True)
bpy.context.view_layer.objects.active = sandblock

# Bake physics to keyframes (so the animation works standalone)
bpy.ops.rigidbody.bake_to_keyframes(
    frame_start=1,
    frame_end=120,
    step=1
)

# ============================================================
# FERTIG! 
# ============================================================
print("=" * 50)
print("SANDBLOCK SZENE FERTIG!")
print("=" * 50)
print(f"Render: Ctrl+F12 oder Render → Render Animation")
print(f"Ausgabe: //renders/sandblock_####.mp4")
print(f"Format: 1080x1920 (9:16), 60fps, 2 Sekunden")
print(f"GPU: Cycles mit CUDA")
print("=" * 50)
