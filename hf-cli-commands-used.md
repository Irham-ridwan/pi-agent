# HF CLI Commands Used in SLM Research

## Instalasi & Setup

```bash
# Install HF CLI
pip install huggingface-hub

# Login (optional untuk public models)
huggingface-cli login

# Atau pakai env var
export HF_TOKEN=hf_xxxxxxxxx
```

## Perintah-perintah Utama

### 1. Mencari Model Berdasarkan Tag

```bash
# Cari model dengan tag tertentu, sort by trending
hf models list --tag "tool-calling" --sort trending_score --limit 50 --format json
hf models list --tag "function-calling" --sort trending_score --limit 50 --format json
hf models list --tag "agent" --sort trending_score --limit 100 --format json
hf models list --tag "agentic" --sort trending_score --limit 50 --format json

# Filter dengan keyword di nama/description
hf models list --search "tool calling" --sort trending_score --limit 50 --format json
hf models list --search "function calling" --sort trending_score --limit 50 --format json
```

### 2. Mencari Model Berdasarkan Keyword

```bash
# Coding models
hf models list --search "code" --sort trending_score --limit 50 --format json
hf models list --search "coder" --sort trending_score --limit 50 --format json
hf models list --search "coding agent" --sort trending_score --limit 30 --format json
hf models list --search "code instruct 3b" --sort trending_score --limit 30 --format json

# Creative writing models
hf models list --search "writing" --sort trending_score --limit 40 --format json
hf models list --search "story" --sort trending_score --limit 40 --format json
hf models list --search "novel" --sort trending_score --limit 30 --format json
hf models list --search "fiction" --sort trending_score --limit 30 --format json
hf models list --search "creative" --sort trending_score --limit 50 --format json
hf models list --search "storytelling" --sort trending_score --limit 30 --format json

# Reasoning / research models
hf models list --search "reasoning" --sort trending_score --limit 50 --format json
hf models list --search "research" --sort trending_score --limit 40 --format json
hf models list --search "RAG" --sort trending_score --limit 40 --format json
hf models list --search "deep research" --sort trending_score --limit 20 --format json

# Community merges / fine-tunes
hf models list --search "merge" --sort trending_score --limit 80 --format json
hf models list --search "distill" --sort trending_score --limit 50 --format json
hf models list --search "opus" --sort trending_score --limit 50 --format json

# Architecture-specific
hf models list --search "Mamba" --sort trending_score --limit 20 --format json
hf models list --search "RWKV" --sort trending_score --limit 20 --format json
```

### 3. Trending Models (Semua)

```bash
# Top 150 trending models
hf models list --sort trending_score --limit 150 --format json

# Trending limited to small models (filter by name pattern via Python)
hf models list --sort trending_score --limit 150 --format json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for m in data:
    pid = m.get('id','').lower()
    likes = m.get('likes',0)
    if likes >= 50 and any(x in pid for x in ['1b','2b','3b','4b','a3b']):
        if not any(x in pid for x in ['12b','13b','20b','27b','30b','32b','70b']):
            print(f\"{m.get('id','?')} | {m.get('downloads',0)} DL | {likes} likes\")
"
```

### 4. Mendapatkan Detail Model

```bash
# Info dasar (metadata, tags, likes, downloads)
hf models info "openbmb/MiniCPM5-1B" --format json

# Model card (README)
hf models card "squ11z1/Mythos-nano" --text
hf models card "Crownelius/Crow-4B-Opus-4.6-Distill-Heretic_Qwen3.5" --text | head -120
```

### 5. Mendapatkan Konfigurasi & Ukuran File

```bash
# Config dari raw file
curl -s "https://huggingface.co/{org}/{repo}/raw/main/config.json"

# File sizes dari API (dengan ?blobs=1 untuk info lengkap)
curl -s "https://huggingface.co/api/models/{org}/{repo}?blobs=1"
```

### 6. Mencari GGUF Variants

```bash
# Cari model dengan GGUF di nama
hf models list --search "GGUF" --sort trending_score --limit 50 --format json
hf models list --search "LocoOperator GGUF" --sort trending_score --limit 20 --format json
hf models list --search "Apodex-1.0-4B" --sort trending_score --limit 10 --format json
```

### 7. Cek Hardware HF Spaces

```bash
hf spaces hardware --format json
```

### 8. Filter Model dari Trending (Script Python Lengkap)

```bash
# Filter: small models (<=4B), rilis dalam 3 bulan terakhir
hf models list --sort trending_score --limit 150 --format json | python3 -c "
import json, sys
from datetime import datetime, timezone
data = json.load(sys.stdin)
cutoff = datetime.now(timezone.utc).timestamp() - 90*86400
for m in data:
    created = m.get('created_at','')
    likes = m.get('likes',0)
    pid = m.get('id','').lower()
    try:
        dt = datetime.fromisoformat(created.replace('Z','+00:00'))
        if dt.timestamp() < cutoff: continue
    except: continue
    if likes < 10: continue
    if any(x in pid for x in ['1b','2b','3b','4b','a3b','0.5b','0.8b','nano','micro','mini','small','tiny']) \
       and not any(x in pid for x in ['12b','13b','20b','27b','30b','32b','70b','8b','9b','7b']):
        print(f\"{m.get('id','?')} | {dt.strftime('%Y-%m-%d')} | {m.get('downloads',0)} DL | {likes} likes\")
"

# Filter: cari model baru yang belum pernah dilihat (60 hari terakhir)
hf models list --sort trending_score --limit 200 --format json | python3 -c "
import json, sys
from datetime import datetime, timezone
data = json.load(sys.stdin)
cutoff = datetime.now(timezone.utc).timestamp() - 60*86400
seen_keywords = ['mythos','apodex','locoperator','minicpm','crow','opus']
for m in data:
    pid = m.get('id','').lower()
    created = m.get('created_at','')
    likes = m.get('likes',0)
    try:
        dt = datetime.fromisoformat(created.replace('Z','+00:00'))
        if dt.timestamp() < cutoff: continue
    except: continue
    if likes < 20: continue
    if not any(x in pid for x in ['1b','2b','3b','4b','a3b']): continue
    if any(x in pid for x in ['12b','13b','20b','27b','30b','32b','70b','8b','9b','7b']): continue
    if any(s in pid for s in seen_keywords): continue
    print(f\"NEW: {m.get('id','?')} | {dt.strftime('%Y-%m-%d')} | {m.get('downloads',0)} DL | {likes} likes\")
"
```

## Alur Riset Lengkap

```
1. hf models list --sort trending_score --limit 150
   -> Lihat landscape trending models

2. Filter by tag: tool-calling, function-calling, agent, agentic
   -> Candidate pool 1: model dengan tool calling capability

3. Filter by search: code, coder, coding
   -> Candidate pool 2: coding-specific models

4. Filter by search: writing, story, novel, creative, fiction
   -> Candidate pool 3: writing models (ternyata sangat sedikit)

5. Filter by search: reasoning, research, deep research
   -> Candidate pool 4: research models

6. Untuk setiap kandidat:
   hf models info "<id>" --format json
   hf models card "<id>" --text | head -X
   curl -s "https://huggingface.co/api/models/<id>?blobs=1"
   
7. Final filter: Q4_K_M size < 16GB, likes >= 10, rilis <= 6 bulan
```
