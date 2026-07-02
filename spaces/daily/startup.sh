#!/bin/sh
# startup.sh — Pi Agent Daily Space
# Warm up model utama (MiniCPM5-1B) saat container start
# agar request pertama tidak timeout

set -e

echo "=== Pi Agent Daily Space Startup ==="
echo "Starting llama-server with MiniCPM5-1B preloaded..."

# Jalankan llama-server dengan 1 model utama yang selalu warm
# --models-dir tetap digunakan agar model lain bisa di-load on-demand
# --model memastikan model utama sudah di-load saat startup
exec llama-server \
  --model /models/MiniCPM5-1B-Q4_K_M.gguf \
  --alias MiniCPM5-1B-Q4_K_M \
  --models-dir /models \
  --host 0.0.0.0 \
  --port 7860 \
  --ctx-size 4096 \
  --n-gpu-layers 0 \
  --parallel 1 \
  --flash-attn \
  --log-prefix
