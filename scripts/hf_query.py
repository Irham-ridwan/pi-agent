#!/usr/bin/env python3
"""
Script untuk query data real dari Hugging Face API.
Digunakan untuk memperkaya laporan riset SLM.
"""

import subprocess
import sys
import json

# Check dan install jika perlu
try:
    from huggingface_hub import HfApi, list_models
    from huggingface_hub.utils import HfHubHTTPError
except ImportError:
    print("Installing huggingface_hub...", flush=True)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "-q", "huggingface_hub"])
    from huggingface_hub import HfApi, list_models
    from huggingface_hub.utils import HfHubHTTPError

import time

api = HfApi()

MODELS_TO_CHECK = [
    # Coding
    "WithinUsAI/Opus4.7-GODs.Ghost.Codex-4B.GGuF",
    "LocoreMind/LocoOperator-4B",
    "HuggingFaceTB/SmolLM3-3B",
    "Qwen/Qwen2.5-Coder-3B-Instruct",
    # Novel
    "Crownelius/Crow-4B-Opus-4.6-Distill-Heretic_Qwen3.5",
    "google/gemma-3-4b-it",
    "mistralai/Ministral-3B-Instruct-2412",
    # Daily
    "openbmb/MiniCPM5-1B",
    "microsoft/Phi-4-mini-instruct",
    "LiquidAI/LFM2.5-1.2B-Instruct",
    # Research
    "squ11z1/Mythos-nano",
    "apodex/Apodex-1.0-4B-SFT",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
    "WeiboAI/VibeThinker-3B",
    # New candidates
    "google/gemma-4-e4b-it",
]

GGUF_REPOS_TO_CHECK = [
    "LocoreMind/LocoOperator-4B-GGUF",
    "openbmb/MiniCPM5-1B-GGUF",
]

def get_model_info(model_id):
    """Get model info dari HF API."""
    try:
        model = api.model_info(model_id)
        info = {
            "id": model.id,
            "likes": model.likes,
            "downloads": model.downloads,
            "tags": model.tags[:10] if model.tags else [],
            "created_at": str(model.created_at)[:10] if model.created_at else "?",
            "last_modified": str(model.last_modified)[:10] if model.last_modified else "?",
            "pipeline_tag": model.pipeline_tag or "?",
            "library_name": model.library_name or "?",
        }
        
        # Check GGUF files
        try:
            files = api.list_repo_files(model_id)
            gguf_files = [f for f in files if f.endswith('.gguf')]
            info["gguf_files"] = gguf_files[:5]  # Max 5
            info["has_gguf"] = len(gguf_files) > 0
        except Exception:
            info["gguf_files"] = []
            info["has_gguf"] = False
        
        return info
    except HfHubHTTPError as e:
        if "404" in str(e):
            return {"id": model_id, "error": "NOT_FOUND"}
        return {"id": model_id, "error": str(e)[:100]}
    except Exception as e:
        return {"id": model_id, "error": str(e)[:100]}

def search_new_models(query, tags=None, limit=10):
    """Cari model baru yang belum ada di laporan."""
    try:
        kwargs = {
            "search": query,
            "sort": "downloads",
            "direction": -1,
            "limit": limit,
        }
        if tags:
            kwargs["tags"] = tags
        
        models = list(list_models(**kwargs))
        results = []
        for m in models:
            results.append({
                "id": m.id,
                "likes": m.likes,
                "downloads": m.downloads,
                "tags": m.tags[:8] if m.tags else [],
                "last_modified": str(m.last_modified)[:10] if m.last_modified else "?",
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]

def get_gguf_file_sizes(repo_id):
    """Get ukuran file GGUF dari repo."""
    try:
        from huggingface_hub import list_repo_tree
        sizes = {}
        for item in list_repo_tree(repo_id):
            if hasattr(item, 'path') and item.path.endswith('.gguf'):
                size_gb = getattr(item, 'size', 0) / (1024**3)
                sizes[item.path] = f"{size_gb:.2f}GB"
        return sizes
    except Exception as e:
        return {"error": str(e)[:80]}

print("=" * 70)
print("HUGGING FACE CLI QUERY — Riset SLM Juli 2026")
print("=" * 70)

# 1. Check semua model utama
print("\n## 1. STATUS MODEL UTAMA\n")
results = {}
for model_id in MODELS_TO_CHECK:
    print(f"  Querying: {model_id}...", end=" ", flush=True)
    info = get_model_info(model_id)
    results[model_id] = info
    if "error" in info:
        print(f"❌ {info['error']}")
    else:
        print(f"✅ likes={info['likes']:,}  downloads={info['downloads']:,}  gguf={info['has_gguf']}")
    time.sleep(0.3)  # Rate limiting

# 2. Print detailed results
print("\n## 2. DETAIL LENGKAP\n")
for model_id, info in results.items():
    print(f"### {model_id}")
    if "error" in info:
        print(f"  ERROR: {info['error']}")
    else:
        print(f"  Likes: {info['likes']:,}")
        print(f"  Downloads: {info['downloads']:,}")
        print(f"  Created: {info['created_at']}")
        print(f"  Modified: {info['last_modified']}")
        print(f"  Pipeline: {info['pipeline_tag']}")
        print(f"  Library: {info['library_name']}")
        print(f"  Tags: {', '.join(info['tags'][:6])}")
        if info['has_gguf']:
            print(f"  GGUF files: {', '.join(info['gguf_files'][:3])}")
        else:
            print(f"  GGUF: Not found in this repo")
    print()

# 3. Search model baru tool-calling
print("\n## 3. MODEL BARU — Tool Calling (Top Downloads)\n")
tool_models = search_new_models("tool calling function calling", tags=["text-generation"], limit=12)
for m in tool_models:
    if "error" not in m:
        print(f"  {m['id'][:55]:<55} likes={m['likes']:>5}  dl={m['downloads']:>8,}  mod={m['last_modified']}")

# 4. Search model baru coding
print("\n## 4. MODEL BARU — Coding SLM ≤4B (Top Downloads)\n")
coding_models = search_new_models("coding instruct 4B", tags=["text-generation"], limit=12)
for m in coding_models:
    if "error" not in m:
        print(f"  {m['id'][:55]:<55} likes={m['likes']:>5}  dl={m['downloads']:>8,}  mod={m['last_modified']}")

# 5. Search model baru reasoning
print("\n## 5. MODEL BARU — Reasoning/Research SLM (Top Downloads)\n")
reason_models = search_new_models("reasoning small 3B 4B", limit=12)
for m in reason_models:
    if "error" not in m:
        print(f"  {m['id'][:55]:<55} likes={m['likes']:>5}  dl={m['downloads']:>8,}  mod={m['last_modified']}")

# 6. Search creative writing models
print("\n## 6. MODEL BARU — Creative Writing (Top Downloads)\n")
creative_models = search_new_models("creative writing instruct", limit=10)
for m in creative_models:
    if "error" not in m:
        print(f"  {m['id'][:55]:<55} likes={m['likes']:>5}  dl={m['downloads']:>8,}  mod={m['last_modified']}")

# 7. Get GGUF file sizes for key repos
print("\n## 7. GGUF FILE SIZES\n")
for repo in GGUF_REPOS_TO_CHECK:
    print(f"  Repo: {repo}")
    sizes = get_gguf_file_sizes(repo)
    if isinstance(sizes, dict) and "error" not in sizes:
        for fname, size in sizes.items():
            print(f"    {fname}: {size}")
    else:
        print(f"    {sizes}")
    print()

# 8. Save raw results
print("\n## 8. RAW JSON OUTPUT\n")
print(json.dumps(results, indent=2, default=str))
