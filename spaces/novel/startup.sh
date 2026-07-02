#!/bin/sh
# startup.sh — Pi Agent Novel Space
# Preload Crow-4B-Opus46 sebagai model utama

set -e
echo "=== Pi Agent Novel Space Startup ==="

exec llama-server \
  --model /models/crow-4b-opus46-Q4_K_M.gguf \
  --alias crow-4b-opus46-Q4_K_M \
  --models-dir /models \
  --host 0.0.0.0 \
  --port 7860 \
  --ctx-size 4096 \
  --n-gpu-layers 0 \
  --parallel 1 \
  --flash-attn \
  --log-prefix
