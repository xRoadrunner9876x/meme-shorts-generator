"""
VoxelSim Video 1: Sandblock fällt (Minimal, Vibrant)
Blender 5.x | EEVEE | Auto Collision Detection

Minimalistisch wie die gehypten Videos:
- 1 Sandblock
- Einfacher Boden
- Vibrante Farben (nicht blass!)
- Saubere Beleuchtung
"""

import bpy
import math
import json
import os
from mathutils import Vector

# ============================================================
# CONFIG
# ============================================================
FPS = 60
DURATION_SEC = 3
TOTAL_FRAMES = FPS * DURATION_SEC
BLOCK_START_Z = 4.0
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "voxelsim_renders")
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
# 2. RENDER SETTINGS (EEVEE)
# ============================================================
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = TOTAL_FRAMES
scene.render.filepath = os.path.join(OUTPUT_DIR, "frame_")
scene.render.image_settings.media_type = 'IMAGE'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'


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


def add_vibrant_mat(obj, name, color, roughness=0.3, metallic=0.0, emission=0.0):
    """Erstellt ein vibrant, nicht-blass Material mit Glanz."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Clear default
    for n in nodes:
        nodes.remove(n)
    
    # Principled BSDF
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    
    # Emission für leuchten (subtil)
    if emission > 0:
        bsdf.inputs['Emission Color'].default_value = color
        bsdf.inputs['Emission Strength'].default_value = emission
    
    # Output
    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    obj.data.materials.append(mat)
    return mat


def add_rb(obj, body_type='ACTIVE', mass=1.0, friction=0.5, restitution=0.0):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.type = body_type
    obj.rigid_body.mass = mass
    obj.rigid_body.friction = friction
    obj.rigid_body.restitution = restitution


# ============================================================
# 4. OBJEKTE — MINIMAL & VIBRANT
# ============================================================

# --- SANDBLOCK (warmes, sattes Gelb-Orange) ---
sandblock = make_cube("Sandblock", (0, 0, BLOCK_START_Z), size=1.0)
sandblock.rotation_euler = (0.12, 0.06, 0.2)
add_vibrant_mat(sandblock, "Sand", 
    color=(0.95, 0.75, 0.30, 1.0),   # Sattes, warmes Gelb-Orange
    roughness=0.25,                     # Glänzend für "satisfying" Look
    metallic=0.0,
    emission=0.15                       # Leichtes Leuchten
)
add_rb(sandblock, 'ACTIVE', mass=5.0, friction=0.6, restitution=0.2)
sandblock.rigid_body.linear_damping = 0.05
sandblock.rigid_body.angular_damping = 0.15

# --- BODEN (tiefes, sattes Grün) ---
ground = make_cube("Ground", (0, 0, -0.75), size=2.0)
ground.scale = (8, 8, 0.75)
add_vibrant_mat(ground, "Grass",
    color=(0.15, 0.55, 0.20, 1.0),    # Tiefes, sattes Grün
    roughness=0.35,
    metallic=0.0
)
add_rb(ground, 'PASSIVE', friction=0.8)

# --- HINTERGRUND-WAND (dunkel, Kontrast) ---
wall = make_cube("BackWall", (0, 6, 2), size=2.0)
wall.scale = (8, 0.5, 6)
add_vibrant_mat(wall, "Wall",
    color=(0.08, 0.08, 0.12, 1.0),    # Fast schwarz, bläulich
    roughness=0.5
)


# ============================================================
# 5. KAMERA (nah, fokussiert, cinematic)
# ============================================================
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 65  # Etwas enger für mehr "Impact"
camera = bpy.data.objects.new("Camera", cam_data)
camera.location = (3.0, -4.0, 4.0)
direction = Vector((0, 0, 1.5)) - camera.location
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(camera)
scene.camera = camera

# ============================================================
# 6. LICHT (warm + cool Kontrast)
# ============================================================
# Key Light (warm, stark)
sun_data = bpy.data.lights.new("KeyLight", 'SUN')
sun_data.energy = 6.0
sun_data.color = (1.0, 0.92, 0.75)     # Warmes Gold
sun = bpy.data.objects.new("KeyLight", sun_data)
sun.location = (4, -2, 8)
sun.rotation_euler = (math.radians(35), math.radians(15), math.radians(25))
scene.collection.objects.link(sun)

# Fill Light (cool, weich)
fill_data = bpy.data.lights.new("FillLight", 'AREA')
fill_data.energy = 400
fill_data.size = 4
fill_data.color = (0.6, 0.7, 1.0)      # Kühles Blau
fill = bpy.data.objects.new("FillLight", fill_data)
fill.location = (-5, -2, 5)
fill.rotation_euler = (math.radians(55), 0, math.radians(-15))
scene.collection.objects.link(fill)

# Rim Light (Akzent, von hinten)
rim_data = bpy.data.lights.new("RimLight", 'AREA')
rim_data.energy = 250
rim_data.size = 2
rim_data.color = (1.0, 0.8, 0.5)       # Warmes Orange
rim = bpy.data.objects.new("RimLight", rim_data)
rim.location = (0, 5, 3)
rim.rotation_euler = (math.radians(-25), math.radians(160), 0)
scene.collection.objects.link(rim)

# ============================================================
# 7. WORLD (dunkler Hintergrund für Kontrast)
# ============================================================
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs['Color'].default_value = (0.05, 0.05, 0.08, 1.0)  # Fast schwarz
bg.inputs['Strength'].default_value = 0.5


# ============================================================
# 8. COLLISION DETECTION
# ============================================================
def detect_collisions():
    collisions = []
    depsgraph = bpy.context.evaluated_depsgraph_get()
    prev_vz = 0
    prev_z = BLOCK_START_Z
    
    for frame in range(1, TOTAL_FRAMES + 1):
        scene.frame_set(frame)
        depsgraph.update()
        obj = depsgraph.objects.get("Sandblock")
        if obj is None:
            continue
        z = obj.matrix_world.translation.z
        vz = (z - prev_z) * FPS
        
        if prev_vz < -0.5 and vz > -0.1:
            collisions.append({
                "frame": frame,
                "time_sec": round(frame / FPS, 3),
                "force": round(abs(prev_vz), 2),
                "type": "impact"
            })
        elif prev_vz < -0.2 and vz > 0 and abs(prev_vz) > abs(vz) * 1.5:
            collisions.append({
                "frame": frame,
                "time_sec": round(frame / FPS, 3),
                "force": round(abs(prev_vz), 2),
                "type": "bounce"
            })
        prev_vz = vz
        prev_z = z
    return collisions


print("Simulating & detecting collisions...")
collisions = detect_collisions()

collision_file = os.path.join(OUTPUT_DIR, "collision_data.json")
with open(collision_file, 'w') as f:
    json.dump({
        "fps": FPS,
        "duration_sec": DURATION_SEC,
        "total_frames": TOTAL_FRAMES,
        "output_dir": OUTPUT_DIR,
        "video_file": os.path.join(OUTPUT_DIR, "animation.mp4"),
        "collisions": collisions
    }, f, indent=2)

print(f"Found {len(collisions)} collision(s):")
for c in collisions:
    print(f"  Frame {c['frame']} ({c['time_sec']}s) - {c['type']} - force: {c['force']}")

scene.frame_set(1)


# ============================================================
# 9. RENDER CALLBACK → AUTO MP4
# ============================================================
def after_render(scene):
    import subprocess
    png_pattern = os.path.join(OUTPUT_DIR, "frame_")
    mp4_path = os.path.join(OUTPUT_DIR, "animation.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", f"{png_pattern}%04d.png",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        mp4_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f"\nMP4: {mp4_path}")
            print(f"Collisions: {collision_file}")
            print(f"\nJetzt: python merge_script.py")
    except Exception as e:
        print(f"Fehler: {e}")

bpy.app.handlers.render_complete.clear()
bpy.app.handlers.render_complete.append(after_render)


# ============================================================
print("=" * 50)
print("VIBRANT SANDBLOCK FERTIG!")
print(f"Output: {OUTPUT_DIR}")
print("F12 = Test | Strg+F12 = Render")
print("=" * 50)
