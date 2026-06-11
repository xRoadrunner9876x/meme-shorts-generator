"""
VoxelSim - Satisfying Physics Simulation Pipeline
Blender 5.x compatible | EEVEE | Auto Collision Detection

1. Script pasten → Run (▶️)
2. F12 = Einzelbild testen
3. Strg+F12 = Render → MP4 + collision_data.json auf Desktop

Output:
  Desktop/voxelsim_renders/frame_####.png  (Einzelbilder)
  Desktop/voxelsim_renders/collision_data.json  (Collision-Timestamps)
  Desktop/voxelsim_renders/animation.mp4  (Video nach Strg+F12)
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
TOTAL_FRAMES = FPS * DURATION_SEC  # 180 Frames
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
# 4. OBJEKTE ERSTELLEN
# ============================================================

# --- Sandblock ---
sandblock = make_cube("Sandblock", (0, 0, BLOCK_START_Z), size=1.0)
sandblock.rotation_euler = (0.15, 0.08, 0.25)
add_mat(sandblock, "Sand", (0.84, 0.72, 0.47, 1.0), 0.85)
add_rb(sandblock, 'ACTIVE', mass=5.0, friction=0.7, restitution=0.15)
sandblock.rigid_body.linear_damping = 0.05
sandblock.rigid_body.angular_damping = 0.2

# --- Boden ---
ground = make_cube("Ground", (0, 0, -1.0), size=2.0)
ground.scale = (10, 10, 1)
add_mat(ground, "Grass", (0.35, 0.55, 0.25, 1.0), 0.9)
add_rb(ground, 'PASSIVE', friction=0.8)

# --- Deko-Blöcke ---
for i, (pos, col, sz) in enumerate([
    ((-3.5, 2, 0), (0.45, 0.32, 0.18, 1.0), 0.6),
    ((3.5, -1.5, 0), (0.50, 0.50, 0.50, 1.0), 0.7),
    ((-2, -3, 0), (0.30, 0.55, 0.28, 1.0), 0.5),
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
camera.location = (4.5, -5.5, 5.5)
direction = Vector((0, 0, 1.5)) - camera.location
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(camera)
scene.camera = camera

# ============================================================
# 6. LICHT
# ============================================================
sun_data = bpy.data.lights.new("Sun", 'SUN')
sun_data.energy = 5.0
sun_data.color = (1.0, 0.95, 0.85)
sun = bpy.data.objects.new("Sun", sun_data)
sun.location = (5, -3, 10)
sun.rotation_euler = (math.radians(40), math.radians(10), math.radians(20))
scene.collection.objects.link(sun)

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
# 8. COLLISION DETECTION
# ============================================================
def detect_collisions():
    """Stepped through the simulation, detects collisions by velocity changes.
    Returns list of collision events with frame numbers and timestamps."""
    
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
        vz = (z - prev_z) * FPS  # velocity in units/sec
        
        # Collision detection:
        # 1. Velocity sign flip (falling → bouncing) = impact
        # 2. Sudden deceleration (big negative → near zero) = settling
        if prev_vz < -0.5 and vz > -0.1:
            # Impact detected!
            timestamp = frame / FPS
            impact_force = abs(prev_vz)  # how fast it was going
            collisions.append({
                "frame": frame,
                "time_sec": round(timestamp, 3),
                "force": round(impact_force, 2),
                "type": "impact",
                "z_position": round(z, 3)
            })
        
        # Secondary bounce detection (smaller bounces)
        elif prev_vz < -0.2 and vz > 0 and abs(prev_vz) > abs(vz) * 1.5:
            timestamp = frame / FPS
            collisions.append({
                "frame": frame,
                "time_sec": round(timestamp, 3),
                "force": round(abs(prev_vz), 2),
                "type": "bounce",
                "z_position": round(z, 3)
            })
        
        prev_vz = vz
        prev_z = z
    
    return collisions


# Step through simulation and detect collisions
print("=" * 50)
print("Simulating physics & detecting collisions...")
collisions = detect_collisions()

# Save collision data
collision_file = os.path.join(OUTPUT_DIR, "collision_data.json")
collision_output = {
    "fps": FPS,
    "duration_sec": DURATION_SEC,
    "total_frames": TOTAL_FRAMES,
    "output_dir": OUTPUT_DIR,
    "video_file": os.path.join(OUTPUT_DIR, "animation.mp4"),
    "collisions": collisions
}

with open(collision_file, 'w') as f:
    json.dump(collision_output, f, indent=2)

print(f"Found {len(collisions)} collision(s):")
for c in collisions:
    print(f"  Frame {c['frame']} ({c['time_sec']}s) - {c['type']} - force: {c['force']}")

# Reset to frame 1 for rendering
scene.frame_set(1)

# ============================================================
# 9. RENDER CALLBACK → AUTO MP4
# ============================================================
def after_render(scene):
    """Called after render completes. Converts PNGs → MP4."""
    import subprocess
    
    png_pattern = os.path.join(OUTPUT_DIR, "frame_")
    mp4_path = os.path.join(OUTPUT_DIR, "animation.mp4")
    
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", f"{png_pattern}%04d.png",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        mp4_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f"\nMP4 ERSTELLT: {mp4_path}")
            print(f"Collision Data: {collision_file}")
            print(f"\nJetzt merge_script.py ausfuehren fuer Sound!")
        else:
            print(f"FFmpeg Fehler: {result.stderr[:200]}")
    except FileNotFoundError:
        print("\nFFmpeg nicht gefunden!")
        print(f"PNGs gespeichert in: {OUTPUT_DIR}")
        print("Manuell: ffmpeg -y -framerate 60 -i frame_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 animation.mp4")
    except Exception as e:
        print(f"Fehler: {e}")


bpy.app.handlers.render_complete.clear()
bpy.app.handlers.render_complete.append(after_render)


# ============================================================
# FERTIG!
# ============================================================
print("=" * 50)
print("SZENE FERTIG!")
print(f"Output: {OUTPUT_DIR}")
print("")
print("F12       = Einzelbild testen")
print("Strg+F12  = Render + Auto MP4 + Collision Data")
print("")
print("Danach: merge_script.py ausfuehren fuer Sound!")
print("=" * 50)
