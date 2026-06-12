"""
Phase 1: Simple falling Minecraft dirt block.
- Single 1x1x1 cube with procedural dirt texture
- Rigid body physics (block falls onto ground plane)
- Clean 3-point lighting
- Camera at satisfying angle
- 60fps, ~3 seconds (180 frames)

Usage: blender --background --python phase1_falling_block.py -- <output.mp4> [frames]
"""
import bpy
import sys
import os
import math

# ─── Parse args ───
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

output_path = argv[0] if len(argv) > 0 else "/tmp/phase1_test.mp4"
total_frames = int(argv[1]) if len(argv) > 1 else 180

print(f"Output: {output_path}")
print(f"Frames: {total_frames}")

# ─── Reset scene completely ───
bpy.ops.wm.read_factory_settings(use_empty=True)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = total_frames
scene.render.fps = 60

# ─── World: dark blue-gray sky ───
world = bpy.data.worlds.new("World")
scene.world = world
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.05, 0.06, 0.1, 1.0)  # dark sky
bg.inputs[1].default_value = 1.0

# ─── Create procedural dirt material ───
def create_dirt_material():
    mat = bpy.data.materials.new("MinecraftDirt")
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (600, 0)

    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (300, 0)
    principled.inputs["Roughness"].default_value = 0.9
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    # Dirt color: warm brown
    base_color = nodes.new("ShaderNodeRGB")
    base_color.location = (-200, 100)
    base_color.outputs[0].default_value = (0.35, 0.2, 0.1, 1.0)

    # Noise for variation
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-200, -100)
    noise.inputs["Scale"].default_value = 15.0
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.7

    # Color ramp: darken some spots
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (0, -100)
    ramp.color_ramp.elements[0].color = (0.15, 0.08, 0.03, 1.0)
    ramp.color_ramp.elements[0].position = 0.4
    ramp.color_ramp.elements[1].color = (0.4, 0.25, 0.12, 1.0)
    ramp.color_ramp.elements[1].position = 0.7

    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], principled.inputs["Base Color"])

    return mat

# ─── Create ground material ───
def create_ground_material():
    mat = bpy.data.materials.new("Ground")
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (400, 0)

    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.location = (200, 0)
    principled.inputs["Roughness"].default_value = 1.0
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    color = nodes.new("ShaderNodeRGB")
    color.location = (0, 0)
    color.outputs[0].default_value = (0.15, 0.15, 0.15, 1.0)
    links.new(color.outputs[0], principled.inputs["Base Color"])

    return mat

# ─── Build scene ───

# Ground plane
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(create_ground_material())

# Ground: rigid body passive (static collider)
bpy.ops.rigidbody.object_add(type='PASSIVE')
ground.rigid_body.collision_shape = 'BOX'
ground.rigid_body.friction = 0.8
ground.rigid_body.restitution = 0.1  # low bounce

# Dirt block - starts above ground
block_size = 1.0
spawn_height = 6.0

bpy.ops.mesh.primitive_cube_add(size=block_size, location=(0, 0, spawn_height + block_size/2))
block = bpy.context.active_object
block.name = "DirtBlock"
block.data.materials.append(create_dirt_material())

# Block: rigid body active (dynamic)
bpy.ops.rigidbody.object_add(type='ACTIVE')
block.rigid_body.mass = 5.0
block.rigid_body.friction = 0.7
block.rigid_body.restitution = 0.15  # slight bounce for satisfaction
block.rigid_body.linear_damping = 0.1
block.rigid_body.angular_damping = 0.3


# ─── Lighting: 3-point setup ───

# Key light (sun, warm)
bpy.ops.object.light_add(type='SUN', location=(5, -3, 10))
key = bpy.context.active_object
key.name = "KeyLight"
key.data.energy = 3.0
key.data.color = (1.0, 0.95, 0.85)
key.data.angle = math.radians(5)
key.rotation_euler = (math.radians(40), math.radians(15), math.radians(-30))

# Fill light (area, cool)
bpy.ops.object.light_add(type='AREA', location=(-4, -2, 5))
fill = bpy.context.active_object
fill.name = "FillLight"
fill.data.energy = 200.0
fill.data.size = 3.0
fill.data.color = (0.7, 0.8, 1.0)
fill.rotation_euler = (math.radians(50), math.radians(-20), 0)

# Rim light (spot, behind)
bpy.ops.object.light_add(type='SPOT', location=(0, 5, 4))
rim = bpy.context.active_object
rim.name = "RimLight"
rim.data.energy = 500.0
rim.data.color = (1.0, 0.9, 0.7)
rim.data.spot_size = math.radians(45)
rim.rotation_euler = (math.radians(60), 0, math.radians(180))

# ─── Camera ───
bpy.ops.object.camera_add(location=(4.5, -4.5, 3.5))
cam = bpy.context.active_object
cam.name = "Camera"
scene.camera = cam

# Point camera at roughly where block will land
cam.constraints.new(type='TRACK_TO')
# Create an empty as target
bpy.ops.object.empty_add(location=(0, 0, 1.0))
target = bpy.context.active_object
target.name = "CamTarget"

track = cam.constraints["Track To"]
track.target = target
track.track_axis = 'TRACK_NEGATIVE_Z'
track.up_axis = 'UP_Y'

# ─── Render settings ───
scene.render.engine = 'BLENDER_EEVEE'
# Render at lower res for CPU rendering, upscale later
scene.render.resolution_x = 270
scene.render.resolution_y = 480  # 9:16 vertical (Shorts)
scene.render.resolution_percentage = 100
scene.render.film_transparent = False

# Render to PNG frames (more robust than direct FFMPEG)
frame_dir = os.path.join(os.path.dirname(output_path), "frames_phase1")
os.makedirs(frame_dir, exist_ok=True)
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.compression = 15
scene.render.filepath = os.path.join(frame_dir, "frame_")

# EEVEE specific
eevee = scene.eevee
eevee.taa_render_samples = 16  # low for CPU rendering speed
eevee.use_fast_gi = True  # global illumination (replaces old AO)
eevee.fast_gi_distance = 2.0
eevee.use_raytracing = True  # screen space reflections/raytracing

# ─── Bake physics ───
# CRITICAL: set physics cache to match our frame range
rbw = scene.rigidbody_world
rbw.point_cache.frame_start = 1
rbw.point_cache.frame_end = total_frames
print(f"Baking physics (frames 1-{total_frames})...")
bpy.ops.ptcache.free_bake_all()
bpy.ops.ptcache.bake_all(bake=True)
print("Physics baked.")

# ─── Render animation (PNG frames) ───
print(f"Rendering {total_frames} frames to {frame_dir}/...")
bpy.ops.render.render(animation=True)
print("Frame rendering complete!")

# ─── Merge frames to MP4 with FFmpeg ───
import subprocess
ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-framerate", "60",
    "-i", os.path.join(frame_dir, "frame_%04d.png"),
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "18",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    output_path
]
print(f"Merging to MP4: {' '.join(ffmpeg_cmd)}")
result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
if result.returncode != 0:
    print(f"FFmpeg error: {result.stderr}")
    sys.exit(1)

# Clean up frames
import shutil
shutil.rmtree(frame_dir, ignore_errors=True)
print(f"Done! Output: {output_path}")
