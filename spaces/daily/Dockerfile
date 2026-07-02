## ── Stage 1: downloader ──────────────────────────────────────────────────────
FROM ubuntu:24.04 AS downloader

RUN apt-get update && apt-get install -y python3-pip && \
    pip install -q --break-system-packages huggingface_hub

RUN mkdir -p /models

# Primary: MiniCPM5-1B — tool calling native, 131K ctx, Apache 2.0 (0.64GB)
RUN hf download openbmb/MiniCPM5-1B-GGUF MiniCPM5-1B-Q4_K_M.gguf --local-dir /models

# Deep Reasoning: Mythos-nano — pure reasoning, MIT, 91.4% AIME25 (1.90GB)
RUN hf download squ11z1/Mythos-nano mythos-nano-Q4_K_M.gguf --local-dir /models

# Function Calling: Nova-FC 1.2B — 97% syntax reliability (0.73GB)
RUN hf download NovachronoAI/LFM2.5-1.2B-Nova-Function-Calling-GGUF \
    LFM2.5-1.2B-Nova-Function-Calling.Q4_K_M.gguf --local-dir /models

# Quick Reasoning: DeepSeek-R1-1.5B — lightweight CoT (1.10GB)
RUN hf download unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF \
    DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf --local-dir /models

# Math: Phi-4-mini-instruct — reasoning (2.50GB)
RUN hf download MaziyarPanahi/Phi-4-mini-instruct-GGUF \
    Phi-4-mini-instruct.Q4_K_M.gguf --local-dir /models

## ── Stage 2: server ──────────────────────────────────────────────────────────
FROM ghcr.io/ggml-org/llama.cpp:server

COPY --chown=1000:1000 --from=downloader /models /models

EXPOSE 7860

CMD ["--model", "/models/MiniCPM5-1B-Q4_K_M.gguf", \
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
