"""
VoxelSim - Preview: Rendert 1 Frame (nach Impact) und öffnet es.

Usage:
  blender --background --python preview.py
"""

import bpy
import os
import sys
import re

DESKTOP = os.path.join(os.path.expanduser("~"), "Desktop")
OUTPUT_DIR = os.path.join(DESKTOP, "voxelsim_renders", "preview")
os.makedirs(OUTPUT_DIR, exist_ok=True)

PREVIEW_FILE = os.path.join(OUTPUT_DIR, "preview.png")

# ============================================================
# Pipeline-Code direkt einbetten (gleiche Szene wie Scene 1)
# ============================================================
import math
import json
import random
from mathutils import Vector

FPS = 60
TOTAL_FRAMES = 70  # Nur bis Frame 70 (nach Impact)
BLOCK_START_Z = 5.0
NUM_PARTICLES = 30
PARTICLE_SIZE = 0.10

# Szene leeren
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for coll in [bpy.data.meshes, bpy.data.materials, bpy.data.cameras,
             bpy.data.lights, bpy.data.worlds]:
    for item in coll:
        coll.remove(item)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = TOTAL_FRAMES

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

# --- Block ---
sandblock = make_cube("Sandblock", (0, 0, BLOCK_START_Z), size=1.0)
sandblock.rotation_euler = (0.12, 0.06, 0.2)
add_vibrant_mat(sandblock, "Sand", (0.95, 0.75, 0.30, 1.0), 0.25, 0.15)
add_rb(sandblock, 'ACTIVE', mass=5.0, friction=0.6, restitution=0.15)
sandblock.rigid_body.linear_damping = 0.05
sandblock.rigid_body.angular_damping = 0.15

# --- Partikel ---
random.seed(42)
sand_colors = [(0.95, 0.75, 0.30, 1.0), (0.85, 0.65, 0.25, 1.0), (0.75, 0.55, 0.20, 1.0)]
particles = []
for i in range(NUM_PARTICLES):
    p = make_cube(f"Sand_{i}", (0, 0, 0), size=PARTICLE_SIZE)
    p.rotation_euler = (random.uniform(0, math.pi), random.uniform(0, math.pi), random.uniform(0, math.pi))
    add_vibrant_mat(p, f"SandMat_{i}", random.choice(sand_colors), 0.3, 0.05)
    add_rb(p, 'ACTIVE', mass=0.1, friction=0.5, restitution=0.3)
    p.rigid_body.linear_damping = 0.1
    p.rigid_body.angular_damping = 0.2
    p.hide_viewport = True
    p.hide_render = True
    p.rigid_body.enabled = False
    particles.append(p)

# --- Boden + Wand ---
ground = make_cube("Ground", (0, 0, -0.75), size=2.0)
ground.scale = (10, 10, 0.75)
add_vibrant_mat(ground, "Grass", (0.15, 0.55, 0.20, 1.0), 0.35)
add_rb(ground, 'PASSIVE', friction=0.8)

wall = make_cube("BackWall", (0, 8, 2), size=2.0)
wall.scale = (10, 0.5, 6)
add_vibrant_mat(wall, "Wall", (0.08, 0.08, 0.12, 1.0), 0.5)

# --- Kamera ---
cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 55
camera = bpy.data.objects.new("Camera", cam_data)
camera.location = (3.5, -4.5, 4.5)
direction = Vector((0, 0, 1.0)) - camera.location
camera.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(camera)
scene.camera = camera

# --- Licht ---
sun_data = bpy.data.lights.new("KeyLight", 'SUN')
sun_data.energy = 6.0
sun_data.color = (1.0, 0.92, 0.75)
sun = bpy.data.objects.new("KeyLight", sun_data)
sun.location = (4, -2, 8)
sun.rotation_euler = (math.radians(35), math.radians(15), math.radians(25))
scene.collection.objects.link(sun)

fill_data = bpy.data.lights.new("FillLight", 'AREA')
fill_data.energy = 400
fill_data.size = 4
fill_data.color = (0.6, 0.7, 1.0)
fill = bpy.data.objects.new("FillLight", fill_data)
fill.location = (-5, -2, 5)
fill.rotation_euler = (math.radians(55), 0, math.radians(-15))
scene.collection.objects.link(fill)

# --- World ---
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs['Color'].default_value = (0.05, 0.05, 0.08, 1.0)
bg.inputs['Strength'].default_value = 0.5

# ============================================================
# Physics simulieren + Collision → Partikel spawnen
# ============================================================
print("Simulating...")
depsgraph = bpy.context.evaluated_depsgraph_get()
prev_vz = 0
prev_z = BLOCK_START_Z
impact_done = False

for frame in range(1, TOTAL_FRAMES + 1):
    scene.frame_set(frame)
    depsgraph.update()
    
    obj = depsgraph.objects.get("Sandblock")
    if obj is None:
        continue
    
    z = obj.matrix_world.translation.z
    vz = (z - prev_z) * FPS
    
    if not impact_done and prev_vz < -0.5 and vz > -0.1:
        impact_done = True
        block_pos = obj.matrix_world.translation.copy()
        
        # Block verstecken
        sandblock.hide_viewport = True
        sandblock.hide_render = True
        sandblock.rigid_body.enabled = False
        
        # Partikel aktivieren
        for p in particles:
            offset = Vector((random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), random.uniform(0.0, 0.4)))
            p.location = block_pos + offset
            p.hide_viewport = False
            p.hide_render = False
            p.rigid_body.enabled = False
            p.rigid_body.type = 'ACTIVE'
            p.rigid_body.enabled = True
        
        # Explosion
        bpy.ops.object.effector_add(type='FORCE', location=block_pos)
        explosion = bpy.context.active_object
        explosion.field.strength = 500.0
        explosion.field.flow = 1.0
        explosion.field.falloff_power = 3.0
        explosion.field.use_max_distance = True
        explosion.field.distance_max = 5.0
        
        print(f"IMPACT at frame {frame}! {NUM_PARTICLES} particles!")
    
    prev_vz = vz
    prev_z = z

# ============================================================
# Frame 70 rendern (nach Impact, Partikel sichtbar)
# ============================================================
scene.frame_set(70)
scene.render.filepath = PREVIEW_FILE
scene.render.image_settings.file_format = 'PNG'

print(f"Rendering preview frame 70 → {PREVIEW_FILE}")
bpy.ops.render.render(write_still=True)

if os.path.exists(PREVIEW_FILE):
    print(f"PREVIEW FERTIG: {PREVIEW_FILE}")
    # Versuche zu öffnen
    try:
        if sys.platform == 'win32':
            os.startfile(PREVIEW_FILE)
        elif sys.platform == 'darwin':
            import subprocess
            subprocess.run(['open', PREVIEW_FILE])
        else:
            import subprocess
            subprocess.run(['xdg-open', PREVIEW_FILE])
    except:
        print(f"(Konnte nicht automatisch öffnen - Datei liegt hier: {PREVIEW_FILE})")
else:
    print("Preview-Datei nicht erstellt!")
