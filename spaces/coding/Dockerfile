## ── Stage 1: downloader ──────────────────────────────────────────────────────
FROM ubuntu:24.04 AS downloader

RUN apt-get update && apt-get install -y python3-pip && \
    pip install -q --break-system-packages huggingface_hub

RUN mkdir -p /models

# Primary: Qwopus3.5-4B-Coder — coding general (Jackrong, Apache 2.0, 2.80GB)
RUN hf download Jackrong/Qwopus3.5-4B-Coder-GGUF Qwopus3.5-4B-coder-Q4_K_M.gguf --local-dir /models

# Premium: Opus4.7 Codex-4B — distilled Claude Opus 4.7 (2.71GB)
RUN hf download WithinUsAI/Opus4.7-GODs.Ghost.Codex-4B.GGuF \
    Opus4.7-Distill-GODsGhost-Codex-4B-Q4_K_M.gguf --local-dir /models

# Agentic: LocoOperator-4B — 100% JSON tool calling, MIT (2.33GB)
RUN hf download LocoreMind/LocoOperator-4B-GGUF LocoOperator-4B.Q4_K_M.gguf --local-dir /models

# Reason: Qwopus3.5-4B-v3 — coding reasoning (2.70GB)
RUN hf download Jackrong/Qwopus3.5-4B-v3-GGUF Qwen3.5-4B.Q4_K_M.gguf --local-dir /models

# Quick: Qwen2.5-Coder-3B — lightweight (official GGUF, 1.90GB)
RUN hf download Qwen/Qwen2.5-Coder-3B-Instruct-GGUF qwen2.5-coder-3b-instruct-q4_k_m.gguf --local-dir /models

## ── Stage 2: server ──────────────────────────────────────────────────────────
FROM ghcr.io/ggml-org/llama.cpp:server

COPY --chown=1000:1000 --from=downloader /models /models

EXPOSE 7860

CMD ["--model", "/models/Qwopus3.5-4B-coder-Q4_K_M.gguf", \
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
