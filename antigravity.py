"""
Pi Agent — Gemini 3.5 + Antigravity Agent Integration
======================================================
Menggunakan Gemini API key untuk akses ke:
  - Gemini 3.5 Flash (text generation, code execution)
  - Antigravity Agent (sandbox coding, file management, web search)
  - NotebookLM-style research via API

Multi-key support: Auto fallback ke key cadangan jika kena rate limit.

Dokumentasi:
  https://ai.google.dev/gemini-api/docs/antigravity-agent
  https://ai.google.dev/gemini-api/docs/interactions-overview

Persyaratan:
  - google-genai >= 2.3.0
  - GEMINI_API_KEY atau GEMINI_API_KEYS environment variable
"""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path
from typing import Optional


# ── Multi-Key Manager ──────────────────────────────────────────────────────────

class _KeyManager:
    """
    Mengelola multiple Gemini API keys dengan auto fallback.

    Urutan key:
      1. Parameter api_key langsung (jika ada)
      2. GEMINI_API_KEYS (env var, dipisah koma)
      3. GEMINI_API_KEY (env var, single key)
      4. GOOGLE_API_KEY (env var, single key)
    """

    def __init__(self, primary_key: Optional[str] = None):
        self._keys: list[str] = []
        self._current_idx = 0

        # Auto-load .env jika belum ada env var (untuk portable setup)
        if not os.environ.get("GEMINI_API_KEYS") and not os.environ.get("GEMINI_API_KEY"):
            env_path = Path(__file__).parent / ".env"
            if env_path.exists():
                for line in open(env_path):
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip("\"'")
                        if k in ("GEMINI_API_KEYS", "GEMINI_API_KEY"):
                            os.environ[k] = v

        # Kumpulkan semua key
        if primary_key:
            self._keys.append(primary_key)

        # GEMINI_API_KEYS — multi-key, dipisah koma
        multi = os.environ.get("GEMINI_API_KEYS", "")
        if multi:
            for k in multi.split(","):
                k = k.strip()
                if k and k not in self._keys:
                    self._keys.append(k)

        # Single key fallback
        for var in ["GEMINI_API_KEY", "GOOGLE_API_KEY"]:
            k = os.environ.get(var, "")
            if k and k not in self._keys:
                self._keys.append(k)

        if not self._keys:
            raise ValueError(
                "GEMINI_API_KEY tidak ditemukan. Set environment variable atau "
                "bikin di https://aistudio.google.com/apikey"
            )

    @property
    def current(self) -> str:
        return self._keys[self._current_idx]

    def fallback(self) -> Optional[str]:
        """Pindah ke key berikutnya. Return None jika habis."""
        if self._current_idx + 1 < len(self._keys):
            self._current_idx += 1
            return self._keys[self._current_idx]
        return None

    def reset(self):
        self._current_idx = 0

    @property
    def count(self) -> int:
        return len(self._keys)

    def __repr__(self) -> str:
        return f"_KeyManager({self.count} keys, active={self._current_idx})"


class Gemini:
    """
    Gemini 3.5 Flash + Antigravity Agent Client.
    Auto fallback ke key cadangan jika kena rate limit.

    Usage:
        g = Gemini()
        g.text("Halo, apa kabar?")
        g.code("Buat fungsi fibonacci dalam Python")
        g.sandbox("Clone repo ini dan jalankan test-nya")

    Multiple API keys:
        export GEMINI_API_KEYS="key1,key2,key3"
        export GEMINI_API_KEY="fallback_single_key"
    """

    def __init__(self, api_key: Optional[str] = None):
        try:
            from google import genai
        except ImportError:
            raise ImportError(
                "Install google-genai: pipx install google-genai"
            )

        self._keyman = _KeyManager(api_key)
        self._genai = genai
        self._client = self._genai.Client(api_key=self._keyman.current)

    def _rotate_key(self) -> bool:
        """Fallback ke key berikutnya. Return False jika habis."""
        next_key = self._keyman.fallback()
        if next_key:
            from google import genai
            self._client = genai.Client(api_key=next_key)
            return True
        return False

    def _call(self, method, *args, **kwargs):
        """
        Wrapper yang auto retry dengan key berikutnya jika kena rate limit.
        Hanya fallback jika masih ada key cadangan yang valid.
        """
        max_fallbacks = self._keyman.count - 1
        for attempt in range(max_fallbacks + 1):
            try:
                return method(*args, **kwargs)
            except Exception as e:
                err_msg = str(e).lower()
                is_rate_limit = any(x in err_msg for x in [
                    "429", "quota", "rate_limit", "rate limit",
                    "resource_exhausted", "too many",
                    "permission_denied", "403",
                ])
                if is_rate_limit and attempt < max_fallbacks:
                    idx_before = self._keyman._current_idx
                    if self._rotate_key():
                        print(f"  ⚡ Key {idx_before + 1} kena limit, fallback ke key {self._keyman._current_idx + 1}...")
                        time.sleep(1)
                        continue
                    # rotate_key returned False — no more keys
                raise
        return None

    # ── Text Generation ─────────────────────────────────────────────────────

    # ── Text Generation ─────────────────────────────────────────────────────

    def text(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Generate teks pakai Gemini 3.5 Flash.
        Cepat, cocok untuk Q&A, summarization, translation.
        """
        contents = []
        if system:
            contents.append({"role": "user", "parts": [{"text": system}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        response = self._call(
            self._client.models.generate_content,
            model="gemini-3.5-flash",
            contents=contents,
        )
        return response.text or ""

    # ── Code Execution ──────────────────────────────────────────────────────

    def code(self, prompt: str) -> str:
        """
        Generate + eksekusi kode Python via Gemini code_execution tool.
        Cocok untuk perhitungan, algoritma, data processing.
        """
        response = self._call(
            self._client.models.generate_content,
            model="gemini-3.5-flash",
            contents=prompt,
            config={"tools": [{"code_execution": {}}]},
        )

        parts = response.candidates[0].content.parts
        output = []
        for part in parts:
            if hasattr(part, "executable_code") and part.executable_code:
                output.append(f"```{part.executable_code.language}\n{part.executable_code.code}\n```")
            elif hasattr(part, "code_execution_result") and part.code_execution_result:
                output.append(f"Result:\n{part.code_execution_result.output}")
            elif hasattr(part, "text") and part.text:
                output.append(part.text)

        return "\n".join(output)

    # ── Antigravity Sandbox ─────────────────────────────────────────────────

    def sandbox(
        self,
        prompt: str,
        tools: Optional[list] = None,
        background: bool = False,
        timeout: int = 300,
        poll_interval: int = 5,
    ) -> str:
        """
        Antigravity Agent — full Linux sandbox DI CLOUD Google.
        Komputer lokal cuma kirim request, semua eksekusi di server Google.

        Kemampuan:
          - Bash, Python, Node.js execution
          - Install packages (pip, npm, apt)
          - File management (read/write/edit/search)
          - Google Search + URL Fetch
          - MCP server support
          - Context compaction otomatis @ ~135K tokens

        Args:
            prompt: Instruksi untuk agent
            tools: Batasi tools (default: all). Contoh: ["google_search", "url_context"]
            background: Eksekusi background (return interaction ID untuk di-poll nanti)
            timeout: Max waktu tunggu (detik)

        Returns:
            Output text atau interaction ID (jika background)

        Contoh:
            g.sandbox("Buat file Python fibonacci.py, jalankan untuk n=10")
            g.sandbox("Clone repo github.com/user/repo, install deps, run tests")
            g.sandbox("Search web untuk AI news terbaru, simpan sebagai markdown")
        """
        params = {
            "agent": "antigravity-preview-05-2026",
            "input": prompt,
            "environment": "remote",
        }

        if tools is not None:
            params["tools"] = [{"type": t} for t in tools]

        if background:
            params["background"] = True

        interaction = self._call(
            self._client.interactions.create,
            **params,
        )

        if background:
            return interaction.id

        # Poll for completion
        start = time.time()
        while interaction.status in ("in_progress", "pending"):
            elapsed = time.time() - start
            if elapsed > timeout:
                raise TimeoutError(
                    f"Antigravity agent timeout after {timeout}s"
                    f" (interaction ID: {interaction.id})"
                )
            time.sleep(poll_interval)
            interaction = self._client.interactions.get(id=interaction.id)

        if interaction.status == "failed":
            raise RuntimeError(
                f"Antigravity agent failed (interaction ID: {interaction.id})"
            )

        return interaction.output_text or ""

    def sandbox_status(self, interaction_id: str) -> dict:
        """Cek status background interaction."""
        interaction = self._client.interactions.get(id=interaction_id)
        return {
            "id": interaction.id,
            "status": interaction.status,
            "output": getattr(interaction, "output_text", ""),
        }

    # ── Multi-turn Conversation ─────────────────────────────────────────────

    def chat(
        self,
        prompt: str,
        previous_id: Optional[str] = None,
        system: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Multi-turn conversation via Interactions API.
        Returns (output_text, interaction_id).

        Gunakan interaction_id sebagai previous_id untuk lanjut chat.
        """
        params = {
            "model": "gemini-3.5-flash",
            "input": prompt,
        }

        if previous_id:
            params["previous_interaction_id"] = previous_id

        if system:
            params["system_instruction"] = system

        interaction = self._call(
            self._client.interactions.create,
            **params,
        )
        return interaction.output_text or "", interaction.id

    # ── Image Understanding ─────────────────────────────────────────────────

    def analyze_image(self, image_path: str, prompt: str) -> str:
        """
        Analyze image dengan Gemini 3.5 Flash.
        Mengirim image sebagai bytes via types.Part.from_bytes()
        (format yang kompatibel dengan google-genai SDK v2.3+).
        """
        from google.genai import types

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        mime_type = self._detect_mime(image_path)
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        response = self._call(
            self._client.models.generate_content,
            model="gemini-3.5-flash",
            contents=[prompt, image_part],
        )
        return response.text or ""

    # ── Utility ─────────────────────────────────────────────────────────────

    @property
    def available_models(self) -> list[str]:
        """List all available models."""
        return self._call(self._client.models.list)

    def auth_status(self) -> str:
        """
        Check API key status. Return string dengan detail semua key.
        """
        lines = []
        for i, k in enumerate(self._keyman._keys):
            is_active = (i == self._keyman._current_idx)
            label = "ACTIVE" if is_active else "cadangan"
            lines.append(f"  Key {i + 1}: {k[:20]}...{k[-4:]} ({label})")
        return "\n".join(lines) + f"\n  Total: {len(self._keyman._keys)} key"

    @property
    def active_key_index(self) -> int:
        """Index key yang sedang aktif."""
        return self._keyman._current_idx + 1

    def reset_keys(self):
        """Reset ke key utama."""
        self._keyman.reset()
        from google import genai
        self._client = genai.Client(api_key=self._keyman.current)

    @staticmethod
    def _detect_mime(path: str) -> str:
        ext = Path(path).suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
        }
        return mime_map.get(ext, "image/png")


# ── Quick Test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    g = Gemini()

    if "--test" in sys.argv:
        print("🔍 Testing Gemini connection...")
        print(g.text("Balas 1 kata: halo"))
        print()

        print("🧪 Testing code execution...")
        print(g.code("Pakai Python: hitung 15 * 37"))
        print()

        print("🧪 Testing antigravity sandbox...")
        print(g.sandbox("Jalankan: echo 'Hello from Antigravity!'"))
        print()

        print("✅ All tests passed!")
