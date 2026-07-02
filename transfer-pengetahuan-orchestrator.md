# Panduan Transfer Pengetahuan — Ekosistem SLM Orchestrator Pi Agent v4.1
**Tanggal:** 2 Juli 2026  
**Lokasi Project:** `/home/smiley/projek/pi`  
**Target OS:** Linux (16GB RAM constraints / HF Spaces CPU-Basic)  
**Tools Utama:** `hf` CLI, `llama-server` (llama.cpp)  

---

## 1. Ringkasan Arsitektur & Filosofi Desain

Untuk menjalankan AI Agent secara lokal/cloud-gratis pada resource terbatas (16GB RAM), kita membagi beban kerja ke dalam **4 Hugging Face Spaces (CPU-Basic gratis, 16GB RAM per Space)**.

Dibandingkan menggunakan engine Python berat seperti `vllm` atau API komersial, kita menggunakan **`llama-server` (llama.cpp)** sebagai backend inferensi karena:
1. **Ultra-ringan:** Ditulis dalam C++, alokasi RAM murni untuk model GGUF tanpa overhead Python.
2. **OpenAI-Compatible:** Menyediakan endpoint REST standard (`/v1/chat/completions`, `/v1/models`).
3. **Native Router Mode:** Menggunakan parameter `--models-dir` dan `--model` untuk melakukan loading model secara dinamis ke RAM (on-demand) dengan mekanisme LRU eviction (`--models-max 2`).
4. **Warmup Native:** Menghindari cold-start timeout Hugging Face Spaces (batas 60 detik) dengan me-preload satu model utama secara native saat container booting.

---

## 2. Struktur Ekosistem HF Spaces

Kita men-deploy 4 Space di bawah akun Hugging Face Anda (`lofox0`):

| Nama Space | Endpoint API | Model Utama (Preloaded) | Model Pendukung (On-Demand) | Status |
|---|---|---|---|---|
| **`pi-daily`** | `https://lofox0-pi-daily.hf.space/v1` | `MiniCPM5-1B-Q4_K_M` | `SmolLM3-Q4_K_M`, `Phi-4-mini-instruct.Q4_K_M`, `LFM2.5-1.2B-Instruct-Q4_K_M`, `LFM2.5-1.2B-Nova-Function-Calling.Q4_K_M` | **RUNNING** ✅ |
| **`pi-coding`** | `https://lofox0-pi-coding.hf.space/v1` | `Qwopus3.5-4B-coder-Q4_K_M` | `LocoOperator-4B.Q4_K_M`, `Qwen3.5-4B.Q4_K_M` (v3), `qwen2.5-coder-3b-instruct-q4_k_m`, `Opus4.7-Distill-GODsGhost-Codex-4B-Q4_K_M` | **RUNNING** ✅ |
| **`pi-research`** | `https://lofox0-pi-research.hf.space/v1` | `mythos-nano-Q4_K_M` | `vibethinker-3b-q4_k_m`, `DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M` | **RUNNING** ✅ |
| **`pi-novel`** | `https://lofox0-pi-novel.hf.space/v1` | `Crow-4B-Opus-4.6-Distill-Heretic_Qwen3.5.Q4_K_M` | `unsloth.Q4_K_M` (Qwen3-4B-RPG-V2), `Ministral-3-3B-Instruct-2512-Q4_K_M`, `gemma-3-4b-it-Q4_K_M` | **PAUSED** ⏸️ |

> [!IMPORTANT]
> **Perbaikan v4.1 vs v4.0:**
> 1. `Ministral-3B-Instruct-2412` sudah dihapus dari HF (404). Diganti `Ministral-3-3B-Instruct-2512` dari repo resmi mistralai.
> 2. Semua GGUF file names sudah diverifikasi dan diperbaiki — nama file HARUS cocok persis dengan yang ada di repo.
> 3. `Opus4.7-GODs.Ghost.Codex-4B` ditambahkan sebagai model premium coding (Claude Opus 4.7 distill, 94 likes, Q4=2.71GB).
> 4. `Nova-FC 1.2B` ditambahkan untuk daily function calling specialist (97% syntax reliability, Q4=0.73GB).
> 5. `SmolLM3-3B` diresearch diganti dengan `VibeThinker-3B` — lebih cocok untuk general research.

> [!IMPORTANT]  
> **Manajemen Kuota Hugging Face Free Tier:**  
> Hugging Face membatasi maksimal **3 Space CPU-Basic aktif (running)** secara bersamaan untuk akun gratis. Oleh karena itu, **`pi-novel` sengaja di-pause** agar daily, coding, dan research bisa berjalan bersamaan. Jika ingin menggunakan novel, Anda harus men-pause salah satu Space lainnya terlebih dahulu:
> ```bash
> hf spaces pause lofox0/pi-research
> hf spaces restart lofox0/pi-novel
> ```

---

## 3. Tabel Referensi GGUF (Verified 2 Juli 2026)

Semua model menggunakan format GGUF Q4_K_M untuk keseimbangan size vs quality.  
Sumber GGUF diverifikasi langsung dari Hugging Face API.

| Model | Parameter | GGUF Repo | File Name Q4_K_M | Size | License |
|---|---|---|---|---|---|
| MiniCPM5-1B | 1B | openbmb/MiniCPM5-1B-GGUF | MiniCPM5-1B-Q4_K_M.gguf | 0.64GB | Apache 2.0 |
| SmolLM3-3B | 3B | ggml-org/SmolLM3-3B-GGUF | SmolLM3-Q4_K_M.gguf | 1.90GB | Apache 2.0 |
| Phi-4-mini-instruct | 3.8B | MaziyarPanahi/Phi-4-mini-instruct-GGUF | Phi-4-mini-instruct.Q4_K_M.gguf | 2.50GB | MIT |
| LFM2.5-1.2B-Instruct | 1.2B | LiquidAI/LFM2.5-1.2B-Instruct-GGUF | LFM2.5-1.2B-Instruct-Q4_K_M.gguf | 0.73GB | Apache 2.0 |
| LFM2.5-Nova-FC | 1.2B | NovachronoAI/LFM2.5-1.2B-Nova-Function-Calling-GGUF | LFM2.5-1.2B-Nova-Function-Calling.Q4_K_M.gguf | 0.73GB | Apache 2.0 |
| Qwopus3.5-4B-Coder | 4B | Jackrong/Qwopus3.5-4B-Coder-GGUF | Qwopus3.5-4B-coder-Q4_K_M.gguf | 2.80GB | Apache 2.0 |
| Qwopus3.5-4B-v3 | 4B | Jackrong/Qwopus3.5-4B-v3-GGUF | Qwen3.5-4B.Q4_K_M.gguf | 2.70GB | Apache 2.0 |
| Opus4.7 Codex-4B | 4B | WithinUsAI/Opus4.7-GODs.Ghost.Codex-4B.GGuF | Opus4.7-Distill-GODsGhost-Codex-4B-Q4_K_M.gguf | 2.71GB | ? (distill) |
| LocoOperator-4B | 4B | LocoreMind/LocoOperator-4B-GGUF | LocoOperator-4B.Q4_K_M.gguf | 2.33GB | MIT |
| Qwen2.5-Coder-3B | 3B | Qwen/Qwen2.5-Coder-3B-Instruct-GGUF | qwen2.5-coder-3b-instruct-q4_k_m.gguf | 1.90GB | Apache 2.0 |
| Crow-4B-Opus-4.6 | 4B | Crownelius/Crow-4B-Opus-4.6-Distill-Heretic_Qwen3.5 | Crow-4B-Opus-4.6-Distill-Heretic_Qwen3.5.Q4_K_M.gguf | 2.71GB | ? |
| Qwen3-4B-RPG-V2 | 4B | Chun121/Qwen3-4B-RPG-Roleplay-V2 | unsloth.Q4_K_M.gguf | 2.50GB | ? |
| Gemma-3-4B-it | 4B | ggml-org/gemma-3-4b-it-GGUF | gemma-3-4b-it-Q4_K_M.gguf | 2.50GB | Gemma |
| Ministral-3-3B-2512 | 3B | mistralai/Ministral-3-3B-Instruct-2512-GGUF | Ministral-3-3B-Instruct-2512-Q4_K_M.gguf | 2.10GB | MIT |
| Mythos-nano | 3B | squ11z1/Mythos-nano (same repo) | mythos-nano-Q4_K_M.gguf | 1.90GB | MIT |
| VibeThinker-3B | 3B | semparuthiveeran/VibeThinker-3B-Q4_K_M-GGUF | vibethinker-3b-q4_k_m.gguf | 1.80GB | MIT |
| DeepSeek-R1-Distill-1.5B | 1.5B | unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF | DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf | 1.10GB | MIT |

**Catatan penting:**
- `mistralai/Ministral-3B-Instruct-2412` sudah **tidak ada** di HF (404). Semua rujukan harus pakai `Ministral-3-3B-Instruct-2512`.
- Beberapa model (Phi-4-mini, LFM2.5, VibeThinker, DeepSeek-R1) tidak punya GGUF resmi dari creator. GGUF diambil dari repositori komunitas terverifikasi.
- LocoOperator-4B punya GGUF di repo terpisah (`LocoreMind/LocoOperator-4B-GGUF`), bukan di repo utama.

---

## 4. Best Practices Dockerfile untuk HF Spaces (Pelajaran Penting)

Saat men-deploy Docker container di Hugging Face Spaces, ada dua aturan kritis:

1. **Permission File (Isu Owner Non-Root):**  
   Hugging Face Spaces menjalankan container menggunakan non-root user dengan **UID 1000**. Model yang kita unduh di stage `downloader` (sebagai root) harus diserah-terimakan dengan permission yang tepat ke user 1000 menggunakan flag `--chown=1000:1000`. Jika tidak, server akan crash silent (Permission Denied).
   ```dockerfile
   COPY --chown=1000:1000 --from=downloader /models /models
   ```
2. **Bypass CMD Wrapper & Preload Native:**  
   Image resmi `ghcr.io/ggml-org/llama.cpp:server` memiliki `ENTRYPOINT ["/app/llama-server"]`. Kita **tidak boleh** menimpa entrypoint tersebut dengan shell script buatan sendiri. Kita cukup mengirim argumen murni lewat `CMD` agar diproses langsung secara native:
   ```dockerfile
   CMD ["--model", "/models/MiniCPM5-1B-Q4_K_M.gguf", "--models-dir", "/models", "--host", "0.0.0.0", "--port", "7860"]
   ```

**Template Dockerfile per Space:**

```dockerfile
FROM --platform=linux/amd64 ghcr.io/ggml-org/llama.cpp:server AS downloader

# Ganti dengan model GGUF yang diinginkan
RUN pip install -q huggingface_hub && \
    huggingface-cli download <GGUF_REPO> <FILE_NAME.gguf> --local-dir /models --local-dir-use-symlinks False

FROM ghcr.io/ggml-org/llama.cpp:server

COPY --chown=1000:1000 --from=downloader /models /models

CMD ["--model", "/models/<PRIMARY_MODEL.gguf>", \
     "--models-dir", "/models", \
     "--host", "0.0.0.0", "--port", "7860", \
     "--models-max", "2", \
     "--no-mmap"]
```

---

## 5. Cara Penggunaan Orchestrator (`orchestrator.py`)

File `orchestrator.py` v4.1 bertindak sebagai pintu gerbang pintar yang mendistribusikan request ke Space yang tepat sesuai jenis tugas.

### Inisialisasi:
```python
from orchestrator import Pi

pi = Pi()  # default HF user: lofox0

# Periksa status kesehatan semua endpoint
print(pi.health())
```

### 1. Tugas Harian & Logika Dasar (Daily Space)
Menggunakan model ringan yang sangat cepat:
```python
# Cepat & instan (MiniCPM5-1B, 0.64GB, tool calling native)
jawaban_cepat = pi.ask("Siapa presiden Indonesia saat ini?")

# Logika / Matematika (Phi-4-mini)
matematika = pi.math("Hitung turunan pertama dari x^2 + 5x - 3")

# Function calling (Nova-FC 1.2B — 97% syntax reliability)
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Dapatkan cuaca",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}}
    }
}]
result = pi.fc("Cuaca di Jakarta?", tools=tools)
```

### 2. Pemrograman & Otomasi (Coding Space)
```python
# Kode Generik (Qwopus3.5-4B-Coder)
kode = pi.code("Buat fungsi rekursif fibonacci di Python")

# Kode Premium (Opus4.7 Codex-4B — distilled dari Claude Opus 4.7)
kode_premium = pi.code("Buat web server Flask dengan 3 endpoint", premium=True)

# Agentic coding dengan tools (LocoOperator-4B — 100% JSON validity)
tools = [{"type": "function", "function": {
    "name": "read_file",
    "description": "Read file content"
}}]
result = pi.agent("Baca file config.json", tools=tools)
```

### 3. Deep Research & Penalaran Logika (Research Space)
```python
# Analisis mendalam (Mythos-nano — 91.4% AIME25)
solusi = pi.solve("Jelaskan paradoks Fermi dan solusi yang paling masuk akal.")

# Riset general (VibeThinker-3B)
riset = pi.research("Sejarah perkembangan AI dari 1950 hingga 2026")

# Riset cepat (DeepSeek-R1-1.5B — lightweight CoT)
cepat = pi.quick_research("Apa itu transformer dalam deep learning?")
```

### 4. Penulisan Novel (Novel Space)
```python
# Chapter novel (Crow-4B-Opus-4.6-Distill — distilled dari Claude Opus 4.6)
chapter = pi.write("Tulis chapter pertama novel fantasi tentang dunia sihir yang hilang.")

# Scene/Roleplay (Qwen3-4B-RPG-V2)
dialog = pi.roleplay("Kamu adalah penyihir tua", "Aku mencari grimoire kuno")
```

---

## 6. Penanganan Khusus: Reasoning Model & CoT (Chain of Thought)

Model reasoning seperti `Mythos-nano`, `VibeThinker-3B`, dan `DeepSeek-R1-1.5B` secara default menghasilkan **proses berpikir** yang sangat panjang sebelum memberikan jawaban akhir.

Pada response JSON API llama-server:
- Proses berpikir disimpan di key **`reasoning_content`** (standar baru OpenAI).
- Jawaban akhir disimpan di key **`content`**.

> [!TIP]  
> **Pencegahan Timeout / Batas Token:**  
> Jika Anda memanggil model reasoning dengan parameter `max_tokens` yang terlalu kecil (misal: 100), seluruh token akan habis digunakan model untuk "berpikir" di `reasoning_content`, membuat field `content` (jawaban akhir) kosong.  
> **Solusi:** Selalu gunakan `max_tokens` minimal **`1024`** atau **`2048`** untuk tugas coding/research agar model memiliki ruang yang cukup untuk menyelesaikan pemikirannya.

---

## 7. Pemeliharaan & Monitoring Tiap 2 Minggu

Untuk memastikan model yang Anda gunakan tetap up-to-date dengan rilis komunitas Hugging Face:

```bash
# Monitor model baru berparameter kecil (<4B) yang sedang trending
hf models ls --sort trending_score --filter text-generation \
  --num-parameters max:4B --limit 10 --expand downloads,likes,trendingScore --format json

# Cek apakah author favorit merilis model baru
hf models ls --author Jackrong --expand downloads,likes --format json
hf models ls --author WeiboAI --expand downloads,likes --format json
```

**Checklist berkala:**
1. Apakah ada model baru dengan likes >500 di kategori <4B?
2. Apakah ada GGUF release baru dari model yang sudah dipakai?
3. Apakah model yang sudah ada masih aktif di HF (tidak 404 seperti Ministral-2412)?
4. Apakah ada model distill baru dari Claude/GPT yang lebih kecil dari 4B?

Jika ingin memperbarui model dalam Space, cukup edit Dockerfile lokal di folder `spaces/<space_name>/Dockerfile`, ganti nama model target di `hf download`, lalu upload ulang:

```bash
hf upload lofox0/pi-<space_name> ./spaces/<space_name>/Dockerfile Dockerfile --repo-type space
```

---

## 8. NotebookLM Research Integration (`research.py`)

File `research.py` menyediakan akses penuh ke NotebookLM untuk web research dan document analysis.

### Cara Pakai:

```python
from orchestrator import Pi

pi = Pi()

# Buat notebook baru
nb = pi.research.create("Riset SLM Model")

# Tambah sumber
pi.research.add_url(nb, "https://huggingface.co/openbmb/MiniCPM5-1B")
pi.research.add_file(nb, "/home/smiley/projek/pi/slm-research-report-juli-2026.md")

# Deep research di web
result = pi.research.deep(nb, "Best small language models for tool calling 2026")

# Tanya NotebookLM tentang hasil riset
answer = pi.research.ask(nb, "Apa kesimpulan utama dari riset ini?")

# Generate report
artifact_id = pi.research.report(nb, fmt="briefing-doc")
pi.research.wait_artifact(nb, artifact_id)
pi.research.download(nb, artifact_id, "./report.md")
```

### Metode yang tersedia:

| Metode | Deskripsi |
|--------|-----------|
| `create(title)` | Buat notebook baru |
| `list()` | List semua notebook |
| `add_url(nb, url)` | Tambah source URL |
| `add_file(nb, path)` | Tambah source file |
| `fast(nb, query)` | Research cepat (detik) |
| `deep(nb, query)` | Research mendalam (15-30 menit) |
| `ask(nb, question)` | Tanya isi notebook |
| `report(nb, fmt)` | Generate report |
| `podcast(nb, instr)` | Generate podcast audio |
| `wait(nb)` | Tunggu research selesai |
| `download(nb, id, path)` | Download artifact |

---

## 9. Catatan Risiko & Mitigasi

### Risiko Model Hilang dari HF
Seperti yang terjadi pada `mistralai/Ministral-3B-Instruct-2412` (404), model bisa tiba-tiba dihapus. Mitigasi:
- Unduh GGUF dan simpan di HF Dataset pribadi sebagai cadangan
- Catat alternatif untuk setiap model
- Jalankan `hf models inspect` setiap 2 minggu

### Risiko RAM Overcommit
Meski 16GB cukup untuk 2 model aktif, pastikan:
- `--models-max 2` di CMD llama-server
- Q4_K_M sebagai standar (bukan Q8_0 atau F16)
- Monitor dengan `hf space logs lofox0/pi-<name> --tail`

### Risiko Cold Start HF Space
HF Spaces CPU-Basic akan tidur setelah 48 jam tidak digunakan. Mitigasi:
- Akses endpoint setiap 12 jam via cron/uptime monitor
- Atau upgrade ke HF Space "CPU-Upgraded" ($0.01/jam) untuk selalu aktif

---

## 9. Perubahan v4.0 → v4.1

| Aspek | v4.0 (sebelum) | v4.1 (setelah riset) | Alasan |
|---|---|---|---|
| Ministral-3B | Ministral-3B-Instruct-2412 ❌ (404) | Ministral-3-3B-Instruct-2512 ✅ | Model lama dihapus HF |
| SmolLM3-3B GGUF | SmolLM3-3B-128K-Q4_K_M ❌ (salah nama) | SmolLM3-Q4_K_M.gguf ✅ | Nama file aktual di GGUF repo |
| Phi-4-mini GGUF | Phi-4-mini-Q4_K_M ❌ (salah nama) | Phi-4-mini-instruct.Q4_K_M.gguf ✅ | Nama file aktual |
| LocoOperator GGUF | LocoOperator-4B.IQ4_XS (IQ4 bukan Q4) | LocoOperator-4B.Q4_K_M.gguf ✅ | Konsistensi Q4_K_M |
| Qwen3-4B-RPG GGUF | qwen3-4b-rpg-v2.Q4_K_M ❌ | unsloth.Q4_K_M.gguf ✅ | Nama file aktual |
| DeepSeek-R1 GGUF | DeepSeek-R1-1.5B-Q4_K_M ❌ | DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf ✅ | Nama file aktual |
| Coding premium | Tidak ada | Opus4.7 Codex-4B ✅ | Distilasi Claude Opus 4.7 |
| Daily FC | Tidak ada | Nova-FC 1.2B ✅ | Function calling specialist |
| Routing task | 3 level (quick/normal/deep) | 4 level (+premium untuk codex) | Premium coding path |

---
*Dokumen Handover & Transfer Pengetahuan untuk Pi Agent v4.1. Seluruh sistem dan referensi model terverifikasi per 2 Juli 2026.*
