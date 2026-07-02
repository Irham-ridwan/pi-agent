## ── Stage 1: downloader ──────────────────────────────────────────────────────
FROM ubuntu:24.04 AS downloader

RUN apt-get update && apt-get install -y python3-pip && \
    pip install -q --break-system-packages huggingface_hub

RUN mkdir -p /models

# Primary: Mythos-nano — pure reasoning, MIT, 91.4% AIME25
RUN hf download squ11z1/Mythos-nano mythos-nano-Q4_K_M.gguf --local-dir /models

# General: VibeThinker-3B — research general (community: semparuthiveeran, 71K downloads)
RUN hf download semparuthiveeran/VibeThinker-3B-Q4_K_M-GGUF vibethinker-3b-q4_k_m.gguf --local-dir /models

# Quick: DeepSeek-R1-1.5B — lightweight CoT (community: unsloth, 76K downloads)
RUN hf download unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF \
    DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf --local-dir /models

## ── Stage 2: server ──────────────────────────────────────────────────────────
FROM ghcr.io/ggml-org/llama.cpp:server

# Gunakan --chown=1000:1000 agar user non-root HF Spaces (UID 1000) bisa membaca model
COPY --chown=1000:1000 --from=downloader /models /models

EXPOSE 7860

# CMD bertindak sebagai argumen default untuk ENTRYPOINT /app/llama-server
CMD ["--model", "/models/mythos-nano-Q4_K_M.gguf", \
     "--models-dir", "/models", \
     "--host", "0.0.0.0", \
     "--port", "7860", \
     "--ctx-size", "8192", \
     "--models-max", "2", \
     "--n-gpu-layers", "0"]
