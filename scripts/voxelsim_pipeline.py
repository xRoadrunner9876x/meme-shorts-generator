"""
VoxelSim - Escalation Video: 1 → 4 → 16 → 50 Blöcke
Ändere SCENE_CONFIG um verschiedene Szenen zu rendern.

Blender 5.x | EEVEE | Auto Collision + Particles
"""

import bpy
import math
import json
import os
import random
from mathutils import Vector

# ============================================================
# CONFIG — HIER SZENE AUSWÄHLEN
# ============================================================
SCENE_ID = 2

SCENES = {
    1: {"blocks": 1,  "name": "1_block",    "particles": 30,  "height": 5.0},
    2: {"blocks": 4,  "name": "4_blocks",   "particles": 60,  "height": 5.0},
    3: {"blocks": 16, "name": "16_blocks",  "particles": 100, "height": 5.0},
    4: {"blocks": 50, "name": "50_blocks",  "particles": 150, "height": 5.0},
}

config = SCENES[SCENE_ID]
NUM_BLOCKS = config["blocks"]
NUM_PARTICLES = config["particles"]
BLOCK_START_Z = config["height"]
SCENE_NAME = config["name"]

FPS = 60
DURATION_SEC = 4
TOTAL_FRAMES = FPS * DURATION_SEC
PARTICLE_SIZE = 0.10

OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "voxelsim_renders", SCENE_NAME)
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
# 2. RENDER SETTINGS
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

# ============================================================
# 3. HELPER
# ============================================================
def make_cube(name, location, size=1.0):
    s = size / 2
    verts = [(-s,-s,-s),(-s,-s,s),(-s,s,-s),(-s,s,s),(s,-s,-s),(s,-s,s),(s,s,-s),(s,s,s)]
    faces = [(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    scene.collection.objects.link(obj)
    return obj

def add_vibrant_mat(obj, name, color, roughness=0.3, emission=0.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for n in nodes:
        nodes.remove(n)
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    if emission > 0:
        bsdf.inputs['Emission Color'].default_value = color
        bsdf.inputs['Emission Strength'].default_value = emission
    output = nodes.new('ShaderNodeOutputMaterial')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    obj.data.materials.append(mat)

def add_rb(obj, body_type='ACTIVE', mass=1.0, friction=0.5, restitution=0.0):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.rigidbody.object_add()
    obj.rigid_body.type = body_type
    obj.rigid_body.mass = mass
    obj.rigid_body.friction = friction
    obj.rigid_body.restitution = restitution

# ============================================================
# 4. BLÖCKE ERSTELLEN (mit Abstand je nach Anzahl)
# ============================================================
random.seed(42)

# Grid-Layout für mehrere Blöcke
import math as m
if NUM_BLOCKS == 1:
    positions = [(0, 0)]
else:
    cols = m.ceil(m.sqrt(NUM_BLOCKS))
    spacing = max(0.8, 2.5 / cols)
    positions = []
    for i in range(NUM_BLOCKS):
        row = i // cols
        col = i % cols
        x = (col - cols/2 + 0.5) * spacing
        y = (row - cols/2 + 0.5) * spacing
        positions.append((x, y))

block_colors = [
    (0.95, 0.75, 0.30, 1.0),  # Sand
    (0.85, 0.65, 0.25, 1.0),  # Dunkler Sand
    (0.90, 0.70, 0.28, 1.0),  # Warm
    (0.80, 0.60, 0.22, 1.0),  # Erde
]

blocks = []
for i, (bx, by) in enumerate(positions):
    # Leicht versetzte Start-Höhen für cascade effect
    height_offset = random.uniform(0, 0.5) if NUM_BLOCKS > 1 else 0
    block = make_cube(f"Block_{i}", (bx, by, BLOCK_START_Z + height_offset), size=0.8)
    block.rotation_euler = (
        random.uniform(-0.15, 0.15),
        random.uniform(-0.15, 0.15),
        random.uniform(-0.3, 0.3)
    )
    color = random.choice(block_colors)
    add_vibrant_mat(block, f"BlockMat_{i}", color, roughness=0.25, emission=0.12)
    add_rb(block, 'ACTIVE', mass=5.0, friction=0.6, restitution=0.15)
    block.rigid_body.linear_damping = 0.05
    block.rigid_body.angular_damping = 0.15
    blocks.append(block)

# ============================================================
# 5. SAND-PARTIKEL (versteckt)
# ============================================================
sand_colors = [
    (0.95, 0.75, 0.30, 1.0),
    (0.85, 0.65, 0.25, 1.0),
    (0.75, 0.55, 0.20, 1.0),
]

particles = []
for i in range(NUM_PARTICLES):
    p = make_cube(f"Sand_{i}", (0, 0, 0), size=PARTICLE_SIZE)
    p.rotation_euler = (random.uniform(0, m.pi), random.uniform(0, m.pi), random.uniform(0, m.pi))
    color = random.choice(sand_colors)
    add_vibrant_mat(p, f"SandMat_{i}", color, roughness=0.3, emission=0.05)
    add_rb(p, 'ACTIVE', mass=0.1, friction=0.5, restitution=0.3)
    p.rigid_body.linear_damping = 0.1
    p.rigid_body.angular_damping = 0.2
    p.hide_viewport = True
    p.hide_render = True
    p.rigid_body.enabled = False
    particles.append(p)

# ============================================================
# 6. BODEN + WAND
# ============================================================
ground = make_cube("Ground", (0, 0, -0.75), size=2.0)
ground.scale = (10, 10, 0.75)
add_vibrant_mat(ground, "Grass", (0.15, 0.55, 0.20, 1.0), roughness=0.35)
add_rb(ground, 'PASSIVE', friction=0.8)

wall = make_cube("BackWall", (0, 8, 2), size=2.0)
wall.scale = (10, 0.5, 6)
add_vibrant_mat(wall, "Wall", (0.08, 0.08, 0.12, 1.0), roughness=0.5)

# ============================================================
# 7. KAMERA (weiter raus bei mehr Blöcken)
# ============================================================
cam_distance = 4.0 + (NUM_BLOCKS / 10)
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 50
camera = bpy.data.objects.new("Camera", cam_data)
camera.location = (cam_distance * 0.7, -cam_distance, cam_distance * 0.8)
direction = Vector((0, 0, 1.0)) - camera.location
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(camera)
scene.camera = camera

# ============================================================
# 8. LICHT
# ============================================================
sun_data = bpy.data.lights.new("KeyLight", 'SUN')
sun_data.energy = 6.0
sun_data.color = (1.0, 0.92, 0.75)
sun = bpy.data.objects.new("KeyLight", sun_data)
sun.location = (4, -2, 8)
sun.rotation_euler = (m.radians(35), m.radians(15), m.radians(25))
scene.collection.objects.link(sun)

fill_data = bpy.data.lights.new("FillLight", 'AREA')
fill_data.energy = 400
fill_data.size = 4
fill_data.color = (0.6, 0.7, 1.0)
fill = bpy.data.objects.new("FillLight", fill_data)
fill.location = (-5, -2, 5)
fill.rotation_euler = (m.radians(55), 0, m.radians(-15))
scene.collection.objects.link(fill)

# ============================================================
# 9. WORLD
# ============================================================
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs['Color'].default_value = (0.05, 0.05, 0.08, 1.0)
bg.inputs['Strength'].default_value = 0.5

# ============================================================
# 10. COLLISION DETECTION + PARTICLE SPAWN
# ============================================================
def simulate():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    collisions = []
    impacts_done = set()
    prev_vz = {}
    prev_z = {}
    
    for block in blocks:
        prev_vz[block.name] = 0
        prev_z[block.name] = block.location.z
    
    for frame in range(1, TOTAL_FRAMES + 1):
        scene.frame_set(frame)
        depsgraph.update()
        
        for block in blocks:
            if block.name in impacts_done:
                continue
            
            obj = depsgraph.objects.get(block.name)
            if obj is None:
                continue
            
            z = obj.matrix_world.translation.z
            vz = (z - prev_z[block.name]) * FPS
            
            if prev_vz[block.name] < -0.5 and vz > -0.1:
                impacts_done.add(block.name)
                
                # Partikeln pro Block (aufteilen)
                per_block = max(5, NUM_PARTICLES // NUM_BLOCKS)
                start_idx = len(collisions) * per_block
                end_idx = min(start_idx + per_block, NUM_PARTICLES)
                
                block_pos = obj.matrix_world.translation.copy()
                
                # Block verstecken
                block.hide_viewport = True
                block.hide_render = True
                block.rigid_body.enabled = False
                
                # Partikel aktivieren
                for pi in range(start_idx, end_idx):
                    if pi >= len(particles):
                        break
                    p = particles[pi]
                    offset = Vector((
                        random.uniform(-0.3, 0.3),
                        random.uniform(-0.3, 0.3),
                        random.uniform(0.0, 0.4)
                    ))
                    p.location = block_pos + offset
                    p.hide_viewport = False
                    p.hide_render = False
                    p.rigid_body.enabled = False
                    p.rigid_body.type = 'ACTIVE'
                    p.rigid_body.enabled = True
                
                # Explosion
                bpy.ops.object.effector_add(type='FORCE', location=block_pos)
                explosion = bpy.context.active_object
                explosion.field.strength = 500.0 + NUM_BLOCKS * 10
                explosion.field.flow = 1.0
                explosion.field.falloff_power = 3.0
                explosion.field.use_max_distance = True
                explosion.field.distance_max = 5.0
                
                collisions.append({
                    "frame": frame,
                    "time_sec": round(frame / FPS, 3),
                    "force": round(abs(prev_vz[block.name]), 2),
                    "type": "impact",
                    "block": block.name
                })
                
                print(f"  {block.name} IMPACT frame {frame} ({round(frame/FPS, 2)}s)")
            
            prev_vz[block.name] = vz
            prev_z[block.name] = z
    
    return collisions


print(f"Scene: {SCENE_NAME} ({NUM_BLOCKS} blocks, {NUM_PARTICLES} particles)")
print("Simulating...")
collisions = simulate()

collision_file = os.path.join(OUTPUT_DIR, "collision_data.json")
with open(collision_file, 'w') as f:
    json.dump({
        "scene": SCENE_NAME,
        "fps": FPS,
        "duration_sec": DURATION_SEC,
        "output_dir": OUTPUT_DIR,
        "video_file": os.path.join(OUTPUT_DIR, "animation.mp4"),
        "collisions": collisions
    }, f, indent=2)

print(f"{len(collisions)} collision(s) detected")
scene.frame_set(1)

# ============================================================
# 11. RENDER CALLBACK
# ============================================================
def after_render(scene):
    import subprocess
    mp4_path = os.path.join(OUTPUT_DIR, "animation.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(OUTPUT_DIR, "frame_%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        mp4_path
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if os.path.exists(mp4_path):
            print(f"\nMP4: {mp4_path}")
    except:
        pass

bpy.app.handlers.render_complete.clear()
bpy.app.handlers.render_complete.append(after_render)

print("=" * 50)
print(f"SCENE '{SCENE_NAME}' FERTIG!")
print(f"Output: {OUTPUT_DIR}")
print(f"Ändere SCENE_ID oben für andere Szenen (1-4)")
print("F12 = Test | Strg+F12 = Render")
print("=" * 50)
