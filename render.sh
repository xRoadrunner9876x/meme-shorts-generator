#!/bin/bash
# Robust Blender render wrapper with upscale
# Usage: ./render.sh <script.py> [output_name] [frames]
set -euo pipefail

SCRIPT="${1:?Usage: ./render.sh <script.py> [output_name] [frames]}"
OUTPUT_NAME="${2:-render}"
FRAMES="${3:-}"

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_PATH="$PROJECT_DIR/scripts/$SCRIPT"
OUTPUT_DIR="$PROJECT_DIR/output"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="$OUTPUT_DIR/${OUTPUT_NAME}_${TIMESTAMP}.mp4"
OUTPUT_1080="$OUTPUT_DIR/${OUTPUT_NAME}_${TIMESTAMP}_1080.mp4"

# Validate script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "ERROR: Script not found: $SCRIPT_PATH"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "=== Blender 5.1.2 Render ==="
echo "Script:  $SCRIPT"
echo "Output:  $OUTPUT_FILE"
echo "Time:    $(date)"

START=$(date +%s)

# Run with xvfb for headless rendering
xvfb-run -a blender --background --python "$SCRIPT_PATH" -- \
    "$OUTPUT_FILE" $FRAMES 2>&1

EXIT_CODE=$?
END=$(date +%s)
DURATION=$((END - START))

if [ $EXIT_CODE -eq 0 ] && [ -f "$OUTPUT_FILE" ]; then
    SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    echo ""
    echo "=== RENDER OK ==="
    echo "File:     $OUTPUT_FILE"
    echo "Size:     $SIZE"
    echo "Duration: ${DURATION}s"
    
    # Upscale to 1080x1920
    echo ""
    echo "=== UPSCALE to 1080x1920 ==="
    ffmpeg -y -i "$OUTPUT_FILE" \
        -vf "scale=1080:1920:flags=lanczos" \
        -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p \
        "$OUTPUT_1080" 2>/dev/null
    
    if [ -f "$OUTPUT_1080" ]; then
        SIZE_1080=$(du -h "$OUTPUT_1080" | cut -f1)
        echo "File:     $OUTPUT_1080"
        echo "Size:     $SIZE_1080"
    fi
else
    echo ""
    echo "=== RENDER FAILED (exit $EXIT_CODE) ==="
    exit 1
fi
