#!/usr/bin/env bash
# Pi Agent — Setup script for fresh clone
set -e

echo "🔧 Pi Agent Setup"
echo "=================="

echo ""
echo "📋 Copy .env from .env.example..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  ✅ .env created"
else
    echo "  ⏭️  .env already exists"
fi

echo ""
echo "📦 Installing Python deps..."
pip3 install --break-system-packages -r requirements.txt 2>/dev/null || pip3 install -r requirements.txt
echo "  ✅ Python dependencies"

echo ""
echo "📦 Installing agentmemory..."
npm install -g @agentmemory/agentmemory 2>/dev/null || npx -y @agentmemory/agentmemory@latest --version
echo "  ✅ agentmemory"

echo ""
echo "🧠 Installing skills..."
npx skills add rohitg00/agentmemory -y 2>/dev/null || true
echo "  ✅ agentmemory skills"

echo ""
echo "📦 Installing google-genai..."
pip install --user --break-system-packages google-genai 2>/dev/null || true

echo ""
echo "✅ Pi Agent siap!"
echo "   Jalankan: python3 -c \"from orchestrator import Pi; pi = Pi(); print(pi.health())\""
echo "   agentmemory: agentmemory &"
