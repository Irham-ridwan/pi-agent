#!/bin/sh
# startup.sh — Pi Agent Research Space
# Preload Mythos-nano sebagai model utama

set -e
echo "=== Pi Agent Research Space Startup ==="

exec llama-server \
  --model /models/mythos-nano-Q4_K_M.gguf \
  --alias mythos-nano-Q4_K_M \
  --models-dir /models \
  --host 0.0.0.0 \
  --port 7860 \
  --ctx-size 4096 \
  --n-gpu-layers 0 \
  --parallel 1 \
  --flash-attn \
  --log-prefix
