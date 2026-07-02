#!/usr/bin/env bash
# Pi Agent — Setup script for fresh clone
# Jalankan: bash setup.sh

set -e

echo "🔧 Pi Agent Setup"
echo "=================="

# 1. Environment
echo ""
echo "📋 Copy .env from .env.example..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  ✅ .env created. Edit with: nano .env"
else
    echo "  ⏭️  .env already exists"
fi

# 2. Python dependencies
echo ""
echo "📦 Installing Python deps..."
pip3 install -r requirements.txt 2>/dev/null || \
pip3 install --break-system-packages -r requirements.txt 2>/dev/null
echo "  ✅ Dependencies installed"

# 3. Optional: Google GenAI SDK
echo ""
echo "📦 Installing google-genai (for Gemini API)..."
pipx install google-genai 2>/dev/null || echo "  ⏭️  Already installed"

# 4. Agent Reach (15 platform channels)
echo ""
echo "📡 Installing Agent Reach..."
pipx install "https://github.com/Panniantong/agent-reach/archive/main.zip" 2>/dev/null
agent-reach install --env=auto 2>/dev/null
echo "  ✅ Agent Reach installed"

# 5. Skills
echo ""
echo "🧠 Installing skills..."
npx skills add google/agents-cli --yes 2>/dev/null || true
npx skills add crewaiinc/skills --yes 2>/dev/null || true
echo "  ✅ Skills installed"

echo ""
echo "✅ Pi Agent siap!"
echo "   Jalankan: python3 -c \"from orchestrator import Pi; pi = Pi(); print(pi.health())\""
echo "   Pastikan GEMINI_API_KEYS diisi di .env"
