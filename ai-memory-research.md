# AI Agent Persistent Memory — Research Report
**Date:** 2 Juli 2026
**Method:** Gemini Research + GitHub API + Hugging Face CLI

---

## Ringkasan Eksekutif

Ditemukan **12 solusi memory persistent** untuk AI agent dengan berbagai pendekatan. Tiga kategori utama:

1. **Production Memory Store** (Zep, Mem0, OpenMemory) — siap pakai, API REST
2. **Autonomous Memory** (Letta/MemGPT, agentmemory) — agent manage memory sendiri
3. **Knowledge Graph Memory** (Graphiti, Memary, Tenure) — relasi antar entitas

---

## Perbandingan Lengkap

| Solusi | Stars | License | Backend | API | Install | Portabilitas |
|--------|-------|---------|---------|-----|---------|-------------|
| **Mem0** | 59.874 | Apache-2.0 | Qdrant/Pgvector/Chroma | Python SDK, REST | `pip install mem0ai` | Lokal + Cloud |
| **Supermemory** | 28.087 | MIT | SQLite/Postgres/Vectorize | REST, JSON API | `git clone + pnpm` | Cloudflare/Docker |
| **Letta (MemGPT)** | 23.621 | Apache-2.0 | PostgreSQL/SQLite | REST, Python, CLI | `pip install letta` | Lokal + Docker |
| **Graphiti** | 28.240 | Apache-2.0 | Neo4j + Vector | Python SDK, REST | `pip install graphiti-sdk` | Docker |
| **Zep** | 4.722 | Apache-2.0 | PostgreSQL (pgvector) | REST, Python/JS SDK | `docker compose up` | Docker + Cloud |
| **OpenMemory** | 4.290 | Apache-2.0 | ? (TypeScript) | REST API | `git clone + npm` | Lokal |
| **Tenurehq/tenure** | 14 | MIT | PostgreSQL/Neo4j | Python SDK, REST | `pip install tenure` | Lokal + Docker |
| **RL-MemoryAgent** | 8 likes (HF) | Apache-2.0 | PyTorch tensor | Python (research) | `git clone` | GPU required |
| **Elias Memory** | 0 likes (HF) | ? | Neo4j + Vector DB | Python SDK | `git clone` | Docker |
| **Memary** | ? | Apache-2.0 | Neo4j + Chroma | Python SDK | `pip install memary` | Docker (Neo4j) |
| **agentmemory** | 40 | MIT | ? (Python) | Python SDK | `pip install` | Lokal |
| **momo** | 38 | MIT | SQLite (Rust) | REST API | Binary download | Lokal (Rust) |

---

## Detail per Solusi

### 1. Mem0 ⭐ 59.874 — Paling Populer
- **Pendekatan:** Hybrid vector + entity graph. Hierarki User → Session → Agent
- **Backend:** Qdrant, Pgvector, Chroma, Pinecone + SQLite/Postgres
- **API:** Python SDK, REST API
- **Install:** `pip install mem0ai`
- **Kelebihan:** Otomatis resolve konflik, update memori tanpa duplikasi, integrasi LangChain/CrewAI
- **Kekurangan:** Hosted cloud mahal di scale besar
- **Lisensi:** Apache-2.0
- **Cocok untuk:** Agent yang butuh memory terstruktur dengan hierarki jelas

### 2. Supermemory ⭐ 28.087 — Second Brain
- **Pendekatan:** Personal knowledge engine, "second brain" untuk AI agent
- **Backend:** Cloudflare D1 (SQLite) / Postgres + Vectorize/Pinecone/Qdrant
- **API:** REST, JSON
- **Install:** `git clone + pnpm install`
- **Kelebihan:** Web extension + UI, edge deployment super cepat
- **Kekurangan:** Heavy tied to Cloudflare ecosystem
- **Lisensi:** MIT
- **Cocok untuk:** Agent yang perlu search over large curated document spaces

### 3. Letta (MemGPT) ⭐ 23.621 — OS-Style Memory
- **Pendekatan:** Virtual memory management: Core Memory (always in context) + Recall Memory (history on disk) + Archival Memory (semantic DB)
- **Backend:** PostgreSQL (pgvector) or SQLite
- **API:** REST, Python SDK, CLI, WebSockets
- **Install:** `pip install letta`
- **Kelebihan:** Paling mature untuk autonomous memory, multi-agent shared memory
- **Kekurangan:** Token consumption tinggi, latency karena tool-calling loops
- **Lisensi:** Apache-2.0
- **Cocok untuk:** Agent yang perlu manage memory sendiri secara otonom

### 4. Graphiti ⭐ 28.240 — Temporal Knowledge Graph
- **Pendekatan:** Dynamic temporal knowledge graph — setiap node/edge punya timestamp
- **Backend:** Neo4j + Vector DB
- **API:** Python SDK, REST
- **Kelebihan:** Tahu kapan fakta menjadi outdated, fast relational retrieval
- **Kekurangan:** Butuh manage graph + vector components
- **Lisensi:** Apache-2.0
- **Cocok untuk:** Agent yang perlu memahami perubahan waktu ("dulu tinggal di X, sekarang di Y")

### 5. Zep ⭐ 4.722 — Production Memory Store
- **Pendekatan:** Enterprise-grade memory store, background auto-summarization + entity extraction
- **Backend:** PostgreSQL (pgvector)
- **API:** REST, Python SDK, JS/TS SDK
- **Install:** `docker compose up`
- **Kelebihan:** High concurrency, async background tasks, SDK lengkap
- **Kekurangan:** Kurang autonomous dibanding Letta
- **Lisensi:** Apache-2.0
- **Cocok untuk:** Production apps dengan traffic tinggi

### 6. OpenMemory ⭐ 4.290 — Local Persistent Memory
- **Pendekatan:** Local persistent memory store untuk LLM apps
- **Bahasa:** TypeScript
- **Support:** Claude Desktop, GitHub Copilot, Codex, Antigravity Agent
- **Backend:** ?
- **Install:** `git clone + npm install`
- **Lisensi:** Apache-2.0
- **Cocok untuk:** Integrasi dengan tools yang sudah ada

### 7. Tenurehq/tenure ⭐ 14 — Entity Resolution
- **Pendekatan:** Long-term memory fokus ke entity resolution & relational integrity
- **Backend:** PostgreSQL (pgvector) atau Neo4j
- **API:** Python SDK, REST
- **Install:** `pip install tenure`
- **Kelebihan:** Entity resolution kuat, cegah duplicate records
- **Kekurangan:** Ekosistem kecil, tutorial minim
- **Lisensi:** MIT

### 8. RL-MemoryAgent — Research (ByteDance/Tsinghua)
- **Pendekatan:** Reinforcement Learning agent yang manage memory storage
- **Backend:** PyTorch tensor
- **Kelebihan:** Optimasi context compression secara ilmiah
- **Kekurangan:** GPU required, research-grade, bukan production
- **Ukuran:** 7B dan 14B parameter
- **Lisensi:** Apache-2.0

### 9. agentmemory (JordanMcCann) ⭐ 40 — #1 LongMemEval
- **Pendekatan:** Memory system untuk AI agents
- **Peringkat:** #1 di LongMemEval — 96.2% (481/500)
- **Mengalahkan:** Chronos, Mastra, dan semua published system
- **Bahasa:** Python
- **Lisensi:** MIT
- **Ukuran:** Kecil, cocok untuk SLM/edge

### 10. momo ⭐ 38 — Rust-based
- **Pendekatan:** Self-hostable AI memory system, inspired by SuperMemory
- **Bahasa:** Rust
- **Backend:** SQLite
- **Kelebihan:** Performa tinggi, binary kecil
- **Lisensi:** MIT

---

## Rekomendasi untuk Pi Agent

### Kriteria:
- Portable (bisa jalan di VPS/Raspberry Pi/CPU basic)
- API-based (biar bisa dipanggil dari orchestrator)
- Minimal dependencies (tidak perlu GPU)
- Open source (bisa di-self-host)
- Ringan (RAM minimal)

### Peringkat:

| Rank | Solusi | Alasan |
|------|--------|--------|
| 🥇 | **Mem0** | Paling populer, hierarki jelas, dokumentasi lengkap, Python native |
| 🥈 | **Letta** | Paling otonom, agent manage memory sendiri, CLI + REST |
| 🥉 | **agentmemory** | #1 LongMemEval, Python, ringan, beats semua saingan |
| 4 | **Zep** | Production-ready, SDK lengkap, async background |
| 5 | **OpenMemory** | TypeScript, support Antigravity & Claude Desktop |

### Kesimpulan untuk Pi Agent:
**Mem0** adalah rekomendasi utama — hierarki memory yang jelas (User/Session/Agent), Python native, portable tanpa GPU, bisa dipanggil via REST API dari orchestrator. Cocok dengan arsitektur Pi Agent yang multi-agent.

**agentmemory** sebagai alternatif ringan — #1 di LongMemEval, lebih kecil dari Mem0, ideal untuk constraint 16GB RAM.

**Letta** untuk autonomous memory — cocok jika agent perlu manage memory sendiri tanpa intervensi manual.
