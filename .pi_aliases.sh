# Pi Agent SLM Orchestrator aliases
# Source this file: source /home/smiley/projek/pi/.pi_aliases.sh

# Quick API tests
alias pi-daily='curl -s "https://lofox0-pi-daily.hf.space/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"MiniCPM5-1B-Q4_K_M.gguf\",\"messages\":[{\"role\":\"user\",\"content\":\"\$*\"}],\"max_tokens\":200}" | python3 -m json.tool'

alias pi-coding='curl -s "https://lofox0-pi-coding.hf.space/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"Qwopus3.5-4B-coder-Q4_K_M.gguf\",\"messages\":[{\"role\":\"user\",\"content\":\"\$*\"}],\"max_tokens\":200}" | python3 -m json.tool'

alias pi-novel='curl -s "https://lofox0-pi-novel.hf.space/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"Crow-4B-Opus-4.6-Distill-Heretic_Qwen3.5.Q4_K_M.gguf\",\"messages\":[{\"role\":\"user\",\"content\":\"\$*\"}],\"max_tokens\":200}" | python3 -m json.tool'

# Health check
alias pi-health='echo "Daily:"; curl -s "https://lofox0-pi-daily.hf.space/v1/models" | python3 -c "import json,sys;d=json.load(sys.stdin);[print(f\"  {m[\"id\"][:50]}\") for m in d.get(\"data\",[])]"; echo "Coding:"; curl -s "https://lofox0-pi-coding.hf.space/v1/models" | python3 -c "import json,sys;d=json.load(sys.stdin);[print(f\"  {m[\"id\"][:50]}\") for m in d.get(\"data\",[])]"; echo "Novel:"; curl -s "https://lofox0-pi-novel.hf.space/v1/models" | python3 -c "import json,sys;d=json.load(sys.stdin);[print(f\"  {m[\"id\"][:50]}\") for m in d.get(\"data\",[])]"'

# Research shortcuts
alias pi-research='notebooklm source add-research'
alias pi-ask-nb='notebooklm ask'
alias pi-nb-list='notebooklm list --json | python3 -c "import json,sys;d=json.load(sys.stdin);[print(f\"{n[\"id\"][:8]} {n[\"title\"]}\") for n in d[\"notebooks\"]]"'
