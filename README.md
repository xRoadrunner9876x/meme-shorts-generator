# 🎮 VoxelSim — Satisfying 3D Physics Shorts

AI-generated Blender simulations for YouTube Shorts.

## Quick Start

```
# 1. Preview (1 Frame anschauen):
blender --background --python preview.py

# 2. Alles rendern (4 Szenen automatisch):
python auto_render.py

# Output: Desktop/voxelsim_renders/final_escalation.mp4
```

## Scripts

| Script | Was es macht |
|--------|-------------|
| `voxelsim_pipeline.py` | Rendert EINE Szene. `SCENE_ID` oben ändern (1-4) |
| `preview.py` | Rendert 1 Frame zum anschauen |
| `auto_render.py` | Rendert alle 4 Szenen + schneidet zusammen |
| `merge_script.py` | Fügt Sound-Effekte an Collision-Stellen hinzu |
| `stitch_videos.py` | Schneidet fertige Szenen zusammen |

## Szenen

- `SCENE_ID=1` → 1 Block fällt, zerfällt in Sand
- `SCENE_ID=2` → 4 Blöcke
- `SCENE_ID=3` → 16 Blöcke  
- `SCENE_ID=4` → 50 Blöcke

## Requirements

- Blender 5.x+
- FFmpeg (für MP4-Konvertierung)
- Python 3.10+
