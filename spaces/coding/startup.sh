#!/bin/sh
# startup.sh — Pi Agent Coding Space
# Preload Qwopus3.5-4B-Coder sebagai model utama

set -e
echo "=== Pi Agent Coding Space Startup ==="

exec llama-server \
  --model /models/Qwopus3.5-4B-coder-Q4_K_M.gguf \
  --alias Qwopus3.5-4B-coder-Q4_K_M \
  --models-dir /models \
  --host 0.0.0.0 \
  --port 7860 \
  --ctx-size 4096 \
  --n-gpu-layers 0 \
  --parallel 1 \
  --flash-attn \
  --log-prefix
