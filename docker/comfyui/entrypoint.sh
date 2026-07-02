#!/bin/sh
set -e

cd /app/ComfyUI

exec python main.py \
    --listen 0.0.0.0 \
    --port 8188 \
    --fp16-unet \
    "$@"
