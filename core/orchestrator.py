"""
Pi Agent — SLM Orchestrator v4.2
=================================
Arsitektur 3 Spaces aktif + NotebookLM untuk research.

Perubahan v4.1 → v4.2:
  🗑  Research space dihapus → NotebookLM di lokal handle research
  ➕ Mythos-nano + DeepSeek-R1 pindah ke pi-daily
  ➕ pi-novel jadi aktif (3 Spaces sesuai kuota HF free)
  🗑  SmolLM3-3B di-drop (redundan)
  🗑  VibeThinker-3B di-drop (NotebookLM gantikan)
  🗑  Qwopus3.5-4B-v3 di-drop (jarang dipakai)
  ✅ Semua model di pi-daily muat dalam 16GB dengan --models-max 3
  ⚡ Optimasi flags (Juli 2026): --threads 4 --flash-attn on --no-mmap --mlock
  ⚡ Latency turun 2-12x (Daily: 2-15s, Coding: 26-37s, Novel: 25-28s)
  ⚡ Fix: content di `reasoning_content` — _content() helper handle otomatis

Arsitektur v4.2:
  pi-daily  → MiniCPM5-1B + Mythos-nano + Nova-FC + DeepSeek-R1 + Phi-4-mini
  pi-coding → Qwopus3.5-4B-Coder + Opus4.7 Codex + LocoOperator-4B + Qwen2.5-Coder-3B
  pi-novel  → Crow-4B-Opus-4.6 + Qwen3-4B-RPG-V2 + Gemma3-4B + Ministral-3-3B
  LOKAL     → NotebookLM untuk web research & document analysis

Engine: llama.cpp (ghcr.io/ggml-org/llama.cpp:server)
API: OpenAI-compatible REST (/v1/chat/completions, /v1/models)
Model: GGUF Q4_K_M, multi-model Router Mode (max 2 aktif per Space)
"""

from __future__ import annotations
import os
import openai
from dataclasses import dataclass
from typing import Optional, Literal
from enum import Enum

# NotebookLM Research Integration
from core.research import Research as _Research


# ── Constants ──────────────────────────────────────────────────────────────────
HF_USER = os.getenv("HF_SPACE_USER", "lofox0")


class Complexity(Enum):
    QUICK  = "quick"   # target <500ms
    NORMAL = "normal"  # default
    DEEP   = "deep"    # reasoning intensif


@dataclass
class Route:
    """
    Konfigurasi routing untuk satu task type.

    Attributes:
        space:       nama space (coding | novel | daily)
        model:       nama file GGUF — HARUS cocok dengan nama di Dockerfile
        gguf_repo:   repo HF tempat GGUF dihosting
        temperature: sampling temperature
        max_tokens:  max output tokens
    """
    space: str
    model: str
    gguf_repo: str = ""
    temperature: float = 0.6
    max_tokens: int = 2048


# ═══════════════════════════════════════════════════════════════════════════════
# TABEL ROUTING v4.2
# ═══════════════════════════════════════════════════════════════════════════════
# Referensi GGUF (verified 2 Juli 2026):
#
# ┌────────────────────────────┬──────────────────────────────────────┬──────────────────────────────────────┬────────┐
# │ Model                      │ GGUF Repo                           │ Q4_K_M File                         │ Size   │
# ├────────────────────────────┼──────────────────────────────────────┼──────────────────────────────────────┼────────┤
# │ MiniCPM5-1B                │ openbmb/MiniCPM5-1B-GGUF            │ MiniCPM5-1B-Q4_K_M.gguf             │ 0.64GB │
# │ Mythos-nano                │ squ11z1/Mythos-nano                 │ mythos-nano-Q4_K_M.gguf             │ 1.90GB │
# │ Nova-FC 1.2B               │ NovachronoAI/LFM2.5-1.2B-Nova-FC    │ LFM2.5-1.2B-Nova-Function-Calling   │ 0.73GB │
# │ DeepSeek-R1-1.5B           │ unsloth/DeepSeek-R1-Distill-Qwen    │ DeepSeek-R1-Distill-Qwen-1.5B       │ 1.10GB │
# │ Phi-4-mini-instruct        │ MaziyarPanahi/Phi-4-mini-instruct   │ Phi-4-mini-instruct.Q4_K_M          │ 2.50GB │
# │ Qwopus3.5-4B-Coder         │ Jackrong/Qwopus3.5-4B-Coder-GGUF   │ Qwopus3.5-4B-coder-Q4_K_M           │ 2.80GB │
# │ Opus4.7 Codex-4B           │ WithinUsAI/Opus4.7-GODs.Ghost.Codex │ Opus4.7-Distill-GODsGhost-Codex     │ 2.71GB │
# │ LocoOperator-4B            │ LocoreMind/LocoOperator-4B-GGUF    │ LocoOperator-4B.Q4_K_M.gguf         │ 2.33GB │
# │ Qwen2.5-Coder-3B           │ Qwen/Qwen2.5-Coder-3B-Instruct     │ qwen2.5-coder-3b-instruct-q4_k_m    │ 1.90GB │
# │ Crow-4B-Opus-4.6-Distill   │ Crownelius/Crow-4B-Opus-4.6-...    │ Crow-4B-Opus...Q4_K_M.gguf          │ 2.71GB │
# │ Qwen3-4B-RPG-Roleplay-V2   │ Chun121/Qwen3-4B-RPG-Roleplay-V2   │ unsloth.Q4_K_M.gguf                 │ 2.50GB │
# │ Gemma-3-4B-it              │ ggml-org/gemma-3-4b-it-GGUF        │ gemma-3-4b-it-Q4_K_M.gguf           │ 2.50GB │
# │ Ministral-3-3B-Instruct    │ mistralai/Ministral-3-3B-Instruct  │ Ministral-3...-Q4_K_M.gguf          │ 2.10GB │
# └────────────────────────────┴──────────────────────────────────────┴──────────────────────────────────────┴────────┘
# ═══════════════════════════════════════════════════════════════════════════════

ROUTES: dict[tuple, Route] = {

    # ── DAILY SPACE ────────────────────────────────────────────────────────────
    # 5 models, --models-max 2 → max RAM = 0.64 + 2.50 = 3.14GB
    #
    # MiniCPM5-1B      (Q4=0.64GB) — primary, tool calling native, 131K ctx
    # Mythos-nano      (Q4=1.90GB) — deep reasoning, 91.4% AIME25
    # Nova-FC-1.2B     (Q4=0.73GB) — function calling specialist
    # DeepSeek-R1-1.5B (Q4=1.10GB) — quick CoT reasoning
    # Phi-4-mini       (Q4=2.50GB) — math

    ("daily",  "ask",     Complexity.QUICK):  Route("daily", "MiniCPM5-1B-Q4_K_M.gguf",
                                                     gguf_repo="openbmb/MiniCPM5-1B-GGUF",
                                                     max_tokens=512),
    ("daily",  "ask",     Complexity.NORMAL): Route("daily", "MiniCPM5-1B-Q4_K_M.gguf",
                                                     gguf_repo="openbmb/MiniCPM5-1B-GGUF",
                                                     max_tokens=1024),
    ("daily",  "solve",   Complexity.NORMAL): Route("daily", "mythos-nano-Q4_K_M.gguf",
                                                     gguf_repo="squ11z1/Mythos-nano",
                                                     temperature=0.3, max_tokens=4096),
    ("daily",  "solve",   Complexity.DEEP):   Route("daily", "mythos-nano-Q4_K_M.gguf",
                                                     gguf_repo="squ11z1/Mythos-nano",
                                                     temperature=0.2, max_tokens=8192),
    ("daily",  "math",    Complexity.NORMAL): Route("daily", "Phi-4-mini-instruct.Q4_K_M.gguf",
                                                     gguf_repo="MaziyarPanahi/Phi-4-mini-instruct-GGUF"),
    ("daily",  "math",    Complexity.DEEP):   Route("daily", "Phi-4-mini-instruct.Q4_K_M.gguf",
                                                     gguf_repo="MaziyarPanahi/Phi-4-mini-instruct-GGUF",
                                                     temperature=0.3, max_tokens=4096),
    ("daily",  "fc",      Complexity.NORMAL): Route("daily", "LFM2.5-1.2B-Nova-Function-Calling.Q4_K_M.gguf",
                                                     gguf_repo="NovachronoAI/LFM2.5-1.2B-Nova-Function-Calling-GGUF",
                                                     temperature=0.3, max_tokens=1024),
    ("daily",  "reason",  Complexity.QUICK):  Route("daily", "DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf",
                                                     gguf_repo="unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF",
                                                     max_tokens=1024),
    ("daily",  "reason",  Complexity.NORMAL): Route("daily", "DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf",
                                                     gguf_repo="unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF",
                                                     max_tokens=2048),

    # ── CODING SPACE ───────────────────────────────────────────────────────────
    # 4 models, --models-max 2 → max RAM = 2.80 + 2.71 = 5.51GB
    #
    # Qwopus3.5-4B-Coder (Q4=2.80GB) — primary coding
    # Opus4.7 Codex-4B   (Q4=2.71GB) — premium (Claude Opus 4.7 distill)
    # LocoOperator-4B    (Q4=2.33GB) — agentic tool calling
    # Qwen2.5-Coder-3B   (Q4=1.90GB) — quick coding

    ("coding", "generate",  Complexity.NORMAL): Route("coding", "Qwopus3.5-4B-coder-Q4_K_M.gguf",
                                                       gguf_repo="Jackrong/Qwopus3.5-4B-Coder-GGUF"),
    ("coding", "generate",  Complexity.DEEP):   Route("coding", "Qwopus3.5-4B-coder-Q4_K_M.gguf",
                                                       gguf_repo="Jackrong/Qwopus3.5-4B-Coder-GGUF",
                                                       temperature=0.5, max_tokens=4096),
    ("coding", "generate",  "premium"):          Route("coding", "Opus4.7-Distill-GODsGhost-Codex-4B-Q4_K_M.gguf",
                                                       gguf_repo="WithinUsAI/Opus4.7-GODs.Ghost.Codex-4B.GGuF",
                                                       temperature=0.5, max_tokens=4096),
    ("coding", "agent",     Complexity.NORMAL): Route("coding", "LocoOperator-4B.Q4_K_M.gguf",
                                                       gguf_repo="LocoreMind/LocoOperator-4B-GGUF"),
    ("coding", "agent",     Complexity.DEEP):   Route("coding", "LocoOperator-4B.Q4_K_M.gguf",
                                                       gguf_repo="LocoreMind/LocoOperator-4B-GGUF",
                                                       temperature=0.3, max_tokens=4096),
    ("coding", "quick",     Complexity.QUICK):  Route("coding", "qwen2.5-coder-3b-instruct-q4_k_m.gguf",
                                                       gguf_repo="Qwen/Qwen2.5-Coder-3B-Instruct-GGUF",
                                                       max_tokens=1024),

    # ── NOVEL SPACE ────────────────────────────────────────────────────────────
    # 4 models, --models-max 2 → max RAM = 2.71 + 2.50 = 5.21GB
    #
    # Crow-4B-Opus-4.6   (Q4=2.71GB) — primary creative writing
    # Qwen3-4B-RPG-V2    (Q4=2.50GB) — roleplay/dialog
    # Ministral-3-3B     (Q4=2.10GB) — editing
    # Gemma-3-4B         (Q4=2.50GB) — fallback

    ("novel", "chapter",  Complexity.NORMAL): Route("novel", "Crow-4B-Opus-4.6-Distill-Heretic_Qwen3.5.Q4_K_M.gguf",
                                                     gguf_repo="Crownelius/Crow-4B-Opus-4.6-Distill-Heretic_Qwen3.5",
                                                     temperature=0.85, max_tokens=4096),
    ("novel", "chapter",  Complexity.DEEP):   Route("novel", "Crow-4B-Opus-4.6-Distill-Heretic_Qwen3.5.Q4_K_M.gguf",
                                                     gguf_repo="Crownelius/Crow-4B-Opus-4.6-Distill-Heretic_Qwen3.5",
                                                     temperature=0.9,  max_tokens=8192),
    ("novel", "scene",    Complexity.QUICK):  Route("novel", "unsloth.Q4_K_M.gguf",
                                                     gguf_repo="Chun121/Qwen3-4B-RPG-Roleplay-V2",
                                                     temperature=0.9,  max_tokens=1024),
    ("novel", "scene",    Complexity.NORMAL): Route("novel", "unsloth.Q4_K_M.gguf",
                                                     gguf_repo="Chun121/Qwen3-4B-RPG-Roleplay-V2",
                                                     temperature=0.85, max_tokens=2048),
    ("novel", "edit",     Complexity.QUICK):  Route("novel", "Ministral-3-3B-Instruct-2512-Q4_K_M.gguf",
                                                     gguf_repo="mistralai/Ministral-3-3B-Instruct-2512-GGUF",
                                                     temperature=0.5,  max_tokens=1024),
    ("novel", "edit",     Complexity.NORMAL): Route("novel", "Ministral-3-3B-Instruct-2512-Q4_K_M.gguf",
                                                     gguf_repo="mistralai/Ministral-3-3B-Instruct-2512-GGUF",
                                                     temperature=0.5,  max_tokens=2048),
    ("novel", "fallback", Complexity.NORMAL): Route("novel", "gemma-3-4b-it-Q4_K_M.gguf",
                                                     gguf_repo="ggml-org/gemma-3-4b-it-GGUF",
                                                     max_tokens=4096),
    ("novel", "fallback", Complexity.DEEP):   Route("novel", "gemma-3-4b-it-Q4_K_M.gguf",
                                                     gguf_repo="ggml-org/gemma-3-4b-it-GGUF",
                                                     max_tokens=8192),
}

DEFAULT_ROUTE = Route("daily", "MiniCPM5-1B-Q4_K_M.gguf",
                      gguf_repo="openbmb/MiniCPM5-1B-GGUF")


# ── Orchestrator ───────────────────────────────────────────────────────────────

class SLMOrchestrator:
    """
    Pi Agent SLM Orchestrator v4.2

    Mengelola routing request ke 3 HF Spaces:
      - daily  : daily tasks + reasoning + math + function calling
      - coding : code generation + agentic + premium codex
      - novel  : creative writing + roleplay + editing

    Research (web research, document analysis, source aggregation)
    ditangani oleh NotebookLM di lokal.
    """

    BASE_URL = "https://{user}-{space}.hf.space/v1"

    def __init__(self, hf_user: str = HF_USER):
        self.hf_user = hf_user
        self._clients: dict[str, openai.OpenAI] = {}

    def _client(self, space: str) -> openai.OpenAI:
        if space not in self._clients:
            url = self.BASE_URL.format(user=self.hf_user, space=f"pi-{space}")
            self._clients[space] = openai.OpenAI(base_url=url, api_key="none")
        return self._clients[space]

    def _resolve(
        self,
        workflow: str,
        task: str,
        complexity: Complexity = Complexity.NORMAL,
    ) -> Route:
        key = (workflow, task, complexity)
        if key in ROUTES:
            return ROUTES[key]
        for c in [Complexity.NORMAL, Complexity.QUICK, Complexity.DEEP]:
            key = (workflow, task, c)
            if key in ROUTES:
                return ROUTES[key]
        return DEFAULT_ROUTE

    def call(
        self,
        workflow: Literal["coding", "novel", "daily"],
        task: str,
        messages: list[dict],
        complexity: Complexity = Complexity.NORMAL,
        tools: Optional[list] = None,
        stream: bool = False,
        **kwargs,
    ):
        route = self._resolve(workflow, task, complexity)
        client = self._client(route.space)

        params: dict = {
            "model":       route.model,
            "messages":    messages,
            "temperature": kwargs.get("temperature", route.temperature),
            "max_tokens":  kwargs.get("max_tokens",  route.max_tokens),
            "stream":      stream,
        }

        if tools:
            params["tools"] = tools
            params["tool_choice"] = kwargs.get("tool_choice", "auto")

        return client.chat.completions.create(**params)

    def list_models(self, space: str) -> list[str]:
        client = self._client(space)
        response = client.models.list()
        return [m.id for m in response.data]

    def health_check(self) -> dict[str, str]:
        results = {}
        for space in ["coding", "novel", "daily"]:
            try:
                models = self.list_models(space)
                results[f"pi-{space}"] = f"✅ OK ({len(models)} models)"
            except Exception as e:
                results[f"pi-{space}"] = f"❌ {str(e)[:60]}"
        return results


# ── Convenience Shortcuts ──────────────────────────────────────────────────────

class Pi:
    """
    Pi Agent SLM Client v4.2

    Semua method otomatis handle content yang masuk ke `reasoning_content`
    (behavior bawaan llama.cpp untuk model Qwen-based distilled).

    Shortcuts:
      pi.ask()          → MiniCPM5-1B     — daily quick
      pi.solve()        → Mythos-nano     — deep reasoning
      pi.math()         → Phi-4-mini      — math/logic
      pi.fc()           → Nova-FC 1.2B    — function calling
      pi.reason()       → DeepSeek-R1     — quick CoT
      pi.code()         → Qwopus3.5-4B    — coding
      pi.code(premium=True) → Opus4.7 Codex — premium coding
      pi.agent()        → LocoOperator-4B — agentic coding
      pi.write()        → Crow-4B-Opus    — creative writing
      pi.roleplay()     → Qwen3-4B-RPG    — roleplay

    Research via NotebookLM CLI (lokal):
      pi.research.deep(nb_id, "query")
      pi.research.ask(nb_id, "question")
    """

    def __init__(self, hf_user: str = HF_USER):
        self._orch = SLMOrchestrator(hf_user)
        self._state = None        # lazy-loaded SQLite
        self._gemini = None       # lazy-loaded Gemini
        self._research_instance = None  # lazy-loaded NotebookLM

    # ── Helper ───────────────────────────────────────────────────────────────

    @staticmethod
    def _content(msg) -> str:
        """
        Extract content dari response message.
        Handle kasus di mana content ada di `reasoning_content`
        (behavior bawaan llama.cpp untuk reasoning/distilled models).
        """
        c = msg.content or ""
        r = getattr(msg, "reasoning_content", None) or ""
        return c if c else r

    # ── Daily ────────────────────────────────────────────────────────────────

    def ask(self, prompt: str, **kw) -> str:
        """Tanya singkat — MiniCPM5-1B (0.64GB, tool calling native)."""
        r = self._orch.call("daily", "ask", [{"role": "user", "content": prompt}],
                            Complexity.QUICK, **kw)
        return self._content(r.choices[0].message)

    def solve(self, prompt: str, **kw) -> str:
        """Deep reasoning — Mythos-nano (1.90GB, 91.4% AIME25)."""
        r = self._orch.call("daily", "solve", [{"role": "user", "content": prompt}],
                            Complexity.DEEP, **kw)
        return self._content(r.choices[0].message)

    def math(self, prompt: str, **kw) -> str:
        """Math/logika — Phi-4-mini (2.50GB)."""
        r = self._orch.call("daily", "math", [{"role": "user", "content": prompt}],
                            Complexity.DEEP, **kw)
        return self._content(r.choices[0].message)

    def fc(self, prompt: str, tools: list, **kw):
        """Function calling — Nova-FC 1.2B (0.73GB, 97% syntax reliability)."""
        return self._orch.call("daily", "fc", [{"role": "user", "content": prompt}],
                               Complexity.NORMAL, tools=tools, **kw)

    def reason(self, prompt: str, **kw) -> str:
        """Quick CoT reasoning — DeepSeek-R1-1.5B (1.10GB)."""
        r = self._orch.call("daily", "reason", [{"role": "user", "content": prompt}],
                            Complexity.NORMAL, **kw)
        return self._content(r.choices[0].message)

    # ── Coding ───────────────────────────────────────────────────────────────

    def code(self, prompt: str, system: str = "You are an expert programmer.",
             premium: bool = False, **kw) -> str:
        """
        Generate kode.
          default:  Qwopus3.5-4B-Coder (2.80GB)
          premium=True: Opus4.7 Codex-4B (2.71GB, Claude Opus 4.7 distill)
        """
        if premium:
            r = self._orch.call("coding", "generate", [
                {"role": "system", "content": "You are Claude Opus 4.7 distilled, an expert software engineer."},
                {"role": "user",   "content": prompt},
            ], "premium", **kw)
        else:
            r = self._orch.call("coding", "generate", [
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ], Complexity.NORMAL, **kw)
        return self._content(r.choices[0].message)

    def agent(self, prompt: str, tools: list, **kw):
        """Agentic coding — LocoOperator-4B (2.33GB, 100% JSON validity)."""
        return self._orch.call("coding", "agent", [
            {"role": "user", "content": prompt},
        ], Complexity.NORMAL, tools=tools, **kw)

    # ── Novel ────────────────────────────────────────────────────────────────

    def write(self, prompt: str, system: str = "Kamu adalah penulis novel berbakat.",
              **kw) -> str:
        """Tulis chapter — Crow-4B-Opus-4.6 (2.71GB, Opus 4.6 distill)."""
        r = self._orch.call("novel", "chapter", [
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ], Complexity.NORMAL, **kw)
        return self._content(r.choices[0].message)

    def roleplay(self, system: str, user: str, **kw) -> str:
        """Scene/dialog — Qwen3-4B-RPG-V2 (2.50GB)."""
        r = self._orch.call("novel", "scene", [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ], Complexity.NORMAL, **kw)
        return self._content(r.choices[0].message)

    # ── NotebookLM Research ────────────────────────────────────────────────

    @property
    def research(self) -> _Research:
        """NotebookLM research tool untuk web research & document analysis."""
        return _Research()

    # ── Gemini / Antigravity Agent ──────────────────────────────────────────

    @property
    def gemini(self) -> 'Gemini':
        """
        Gemini 3.5 Flash + Antigravity Agent.

        Butuh GEMINI_API_KEY environment variable.
        Dapatkan key gratis di https://aistudio.google.com/apikey

        Contoh:
            pi.gemini.text("Summarize this concept")
            pi.gemini.code("Buat fungsi fibonacci")
            pi.gemini.sandbox("Clone repo, install deps, jalankan test")
        """
        try:
            from core.antigravity import Gemini
        except ImportError:
            raise ImportError(
                "File antigravity.py tidak ditemukan. "
                "Pastikan antigravity.py ada di core/."
            )
        return Gemini()

    # ── State Persistence ───────────────────────────────────────────────────

    def _get_state(self) -> 'SessionStore':
        """Lazy-load SessionStore dengan caching (mencegah SQLite connection leak)."""
        if self._state is None:
            try:
                from core.state import SessionStore
            except ImportError:
                raise ImportError(
                    "File state.py tidak ditemukan. Pastikan state.py ada di core/."
                )
            self._state = SessionStore()
        return self._state

    @property
    def state(self) -> 'SessionStore':
        """
        SQLite-based state persistence (connection cached, no leak).

        Data disimpan di ~/.pi/state/sessions.db

        Contoh:
            pi.state.save("last_task", {"workflow": "coding"})
            pi.state.load("last_task")
            pi.state.log_session("sess-1", "coding", "Qwopus3.5", "prompt", "response")
        """
        return self._get_state()

    # ── Utility ──────────────────────────────────────────────────────────────

    def health(self) -> dict:
        return self._orch.health_check()

    def models(self, space: str) -> list[str]:
        return self._orch.list_models(space)


# ── CLI / Demo ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    pi = Pi()

    print("🔍 Checking health of all Pi Agent Spaces...")
    status = pi.health()
    for space, s in status.items():
        print(f"  {space}: {s}")

    if "--demo" in sys.argv:
        print("\n💬 Daily — Ask (MiniCPM5-1B):")
        print(pi.ask("Apa ibu kota Indonesia?"))

        print("\n🧠 Daily — Solve (Mythos-nano):")
        print(pi.solve("Berapa jumlah bilangan prima antara 1 dan 100?"))

        print("\n💻 Coding — Premium (Opus4.7 Codex):")
        print(pi.code("Tulis fungsi Python fibonacci rekursif.", premium=True))

        print("\n📖 Novel — Write (Crow-4B-Opus):")
        print(pi.write("Paragraf pembuka novel detektif di Jakarta 2049."))

        if "--research" in sys.argv:
            print("\n🔬 Research — NotebookLM:")
            print("  Gunakan: pi.research.create('topic')")
            print("           pi.research.deep(nb_id, 'query')")
            print("           pi.research.ask(nb_id, 'question')")
