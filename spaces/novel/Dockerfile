## ── Stage 1: downloader ──────────────────────────────────────────────────────
FROM ubuntu:24.04 AS downloader

RUN apt-get update && apt-get install -y python3-pip && \
    pip install -q --break-system-packages huggingface_hub

RUN mkdir -p /models

# Primary: Crow-4B-Opus-4.6-Distill — creative writing specialist (2.71GB)
RUN hf download Crownelius/Crow-4B-Opus-4.6-Distill-Heretic_Qwen3.5 \
    Crow-4B-Opus-4.6-Distill-Heretic_Qwen3.5.Q4_K_M.gguf --local-dir /models

# Scene/RPG: Qwen3-4B-RPG-Roleplay-V2 — roleplay/dialog (2.50GB)
RUN hf download Chun121/Qwen3-4B-RPG-Roleplay-V2 unsloth.Q4_K_M.gguf --local-dir /models

# Edit: Ministral-3-3B-Instruct-2512 — editing (2.10GB, official mistralai GGUF)
RUN hf download mistralai/Ministral-3-3B-Instruct-2512-GGUF \
    Ministral-3-3B-Instruct-2512-Q4_K_M.gguf --local-dir /models

# Fallback: Gemma-3-4B-it — 128K context (2.50GB, official ggml-org GGUF)
RUN hf download ggml-org/gemma-3-4b-it-GGUF gemma-3-4b-it-Q4_K_M.gguf --local-dir /models

## ── Stage 2: server ──────────────────────────────────────────────────────────
FROM ghcr.io/ggml-org/llama.cpp:server

COPY --chown=1000:1000 --from=downloader /models /models

EXPOSE 7860

CMD ["--model", "/models/Crow-4B-Opus-4.6-Distill-Heretic_Qwen3.5.Q4_K_M.gguf", \
     "--models-dir", "/models", \
     "--host", "0.0.0.0", \
     "--port", "7860", \
     "--ctx-size", "8192", \
     "--models-max", "3", \
     "--threads", "4", \
     "--flash-attn", "on", \
     "--no-mmap", \
     "--mlock", \
     "--cont-batching", \
     "--batch-size", "2048", \
     "--ubatch-size", "512", \
     "--n-gpu-layers", "0"]
