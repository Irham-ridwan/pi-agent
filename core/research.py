"""
Pi Agent — NotebookLM Research Integration v4.2
===============================================
Integrasi NotebookLM sebagai mesin research untuk Pi Agent.
Semua fungsi memanggil `notebooklm` CLI via subprocess.

Flow riset:
  1. Buat notebook → notebooklm create "Topic"
  2. Tambah sumber → notebooklm source add URL/file
  3. Deep research → notebooklm source add-research "query" --mode deep
  4. Query → notebooklm ask "pertanyaan"
  5. Generate report → notebooklm generate report --format briefing-doc
  6. Download → notebooklm download report ./output.md

Persyaratan:
  - notebooklm-py v0.7.3 terinstall (via uv tool)
  - Sudah login: notebooklm login
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional


# ── Constants ──────────────────────────────────────────────────────────────────

NOTEBOOKLM_BIN = "notebooklm"
NOTEBOOKS_DIR = Path.home() / "projek" / "pi" / "research"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _run(*args: str, timeout: int = 60, input_data: Optional[str] = None) -> dict:
    """
    Jalankan perintah notebooklm CLI, parse JSON output.

    Args:
        *args: argumen CLI (tanpa 'notebooklm')
        timeout: timeout dalam detik
        input_data: stdin input (opsional)

    Returns:
        dict hasil parsing JSON
    """
    cmd = [NOTEBOOKLM_BIN] + list(args)
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            input=input_data,
        )
        if r.returncode != 0:
            return {"error": r.stderr.strip()[:300], "returncode": r.returncode}

        # Gabungkan stdout + stderr, NotebookLM kadang kirim log ke stderr
        combined = r.stdout + "\n" + r.stderr

        # Cari JSON object pertama (mulai dengan {) di seluruh output
        for line in combined.split("\n"):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                return json.loads(line)

        # Jika tidak nemu JSON utuh dalam satu line, coba multi-line
        # Cari posisi { pertama dan } terakhir
        start = combined.find("{")
        end = combined.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(combined[start:end+1])
            except json.JSONDecodeError:
                pass

        # Fallback: kembalikan stdout mentah
        return {"output": r.stdout.strip()[:500]}

    except subprocess.TimeoutExpired:
        return {"error": f"Timeout after {timeout}s", "returncode": 2}
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}", "raw": r.stdout[:500]}
    except FileNotFoundError:
        return {"error": f"notebooklm CLI tidak ditemukan. Install: uv tool install notebooklm-py[browser]"}


# ── Notebook Management ────────────────────────────────────────────────────────

def create_notebook(title: str) -> str:
    """Buat notebook baru, return ID."""
    r = _run("create", title, "--json")
    if "error" in r:
        raise RuntimeError(f"Gagal buat notebook: {r['error']}")
    return r.get("notebook", {}).get("id", "")


def list_notebooks() -> list[dict]:
    """List semua notebook."""
    r = _run("list", "--json")
    if "error" in r:
        raise RuntimeError(f"Gagal list notebook: {r['error']}")
    return r.get("notebooks", [])


def delete_notebook(notebook_id: str):
    """Hapus notebook."""
    r = _run("delete", "-n", notebook_id, "--yes", "--json")
    if "error" in r:
        raise RuntimeError(f"Gagal hapus notebook: {r['error']}")


# ── Source Management ──────────────────────────────────────────────────────────

def add_source(notebook_id: str, url_or_path: str) -> str:
    """Tambah sumber (URL atau file path), return source ID."""
    r = _run("source", "add", url_or_path, "-n", notebook_id, "--json")
    if "error" in r:
        raise RuntimeError(f"Gagal add source: {r['error']}")
    return r.get("source", {}).get("id", "")


def add_url_source(notebook_id: str, url: str) -> str:
    """Tambah URL source."""
    return add_source(notebook_id, url)


def add_file_source(notebook_id: str, filepath: str) -> str:
    """Tambah file source (PDF, MD, txt, dll)."""
    return add_source(notebook_id, filepath)


def list_sources(notebook_id: str) -> list[dict]:
    """List semua source di notebook."""
    r = _run("source", "list", "-n", notebook_id, "--json")
    if "error" in r:
        raise RuntimeError(f"Gagal list source: {r['error']}")
    return r.get("sources", [])


# ── Web Research ───────────────────────────────────────────────────────────────

def research_fast(notebook_id: str, query: str, timeout: int = 180) -> list[dict]:
    """
    Research cepat di web (mode fast).
    Blocking sampai selesai.

    Args:
        notebook_id: ID notebook
        query: pertanyaan riset
        timeout: timeout dalam detik (default 3 menit)

    Returns:
        list of source IDs yang terimport
    """
    r = _run("source", "add-research", query, "-n", notebook_id, "--json",
             timeout=timeout)
    if "error" in r:
        if "No result found" in r.get("error", ""):
            print("⚠️  Rate limited. Tunggu 5 menit lalu coba lagi.")
            return []
        raise RuntimeError(f"Research gagal: {r['error']}")
    return r.get("sources", [])


def research_deep(notebook_id: str, query: str, wait: bool = True,
                  timeout: int = 1800) -> str:
    """
    Research mendalam di web (mode deep).

    Args:
        notebook_id: ID notebook
        query: pertanyaan riset
        wait: True = blocking sampai selesai, False = return task ID
        timeout: timeout dalam detik (default 30 menit)

    Returns:
        Jika wait=True: jumlah source terimport
        Jika wait=False: task ID untuk polling
    """
    if wait:
        r = _run("source", "add-research", query, "-n", notebook_id,
                 "--mode", "deep", "--import-all", "--json", timeout=timeout)
        if "error" in r:
            raise RuntimeError(f"Deep research gagal: {r['error']}")
        sources = r.get("sources", [])
        return f"{len(sources)} sources imported"
    else:
        r = _run("source", "add-research", query, "-n", notebook_id,
                 "--mode", "deep", "--no-wait", "--json", timeout=30)
        if "error" in r:
            raise RuntimeError(f"Deep research start gagal: {r['error']}")
        return r.get("poll_id", "") or r.get("task_id", "")


def research_status(notebook_id: str) -> dict:
    """Cek status research yang sedang berjalan."""
    r = _run("research", "status", "-n", notebook_id, "--json")
    if "error" in r:
        return {"status": "unknown", "error": r["error"]}
    return r


def research_wait(notebook_id: str, timeout: int = 1800) -> str:
    """Tunggu research selesai, import semua source."""
    r = _run("research", "wait", "-n", notebook_id, "--import-all",
             "--json", timeout=timeout)
    if "error" in r:
        if "timeout" in r.get("error", "").lower():
            return "Timeout. Coba dengan timeout lebih besar atau cek manual."
        raise RuntimeError(f"Research wait gagal: {r['error']}")
    return f"Research selesai. {r.get('imported_count', '?')} sources imported."


# ── Chat / Query ───────────────────────────────────────────────────────────────

def ask(notebook_id: str, question: str, timeout: int = 120) -> str:
    """
    Tanya NotebookLM tentang isi notebook.

    Args:
        notebook_id: ID notebook
        question: pertanyaan
        timeout: timeout dalam detik

    Returns:
        Jawaban teks
    """
    r = _run("ask", question, "-n", notebook_id, "--json", timeout=timeout)
    if "error" in r:
        raise RuntimeError(f"Query gagal: {r['error']}")
    return r.get("answer", r.get("output", str(r)))


def ask_with_refs(notebook_id: str, question: str, timeout: int = 120) -> dict:
    """Tanya dengan referensi sumber."""
    r = _run("ask", question, "-n", notebook_id, "--json", timeout=timeout)
    if "error" in r:
        raise RuntimeError(f"Query gagal: {r['error']}")
    return r


# ── Report & Artifact Generation ───────────────────────────────────────────────

def generate_report(notebook_id: str, fmt: str = "briefing-doc",
                    append: str = "", timeout: int = 900) -> str:
    """
    Generate report dari notebook.

    Args:
        notebook_id: ID notebook
        fmt: briefing-doc | study-guide | blog-post | custom
        append: instruksi tambahan
        timeout: timeout dalam detik

    Returns:
        Artifact ID
    """
    cmd = ["generate", "report", "--format", fmt, "-n", notebook_id, "--json"]
    if append:
        cmd += ["--append", append]

    r = _run(*cmd, timeout=timeout)
    if "error" in r:
        raise RuntimeError(f"Generate report gagal: {r['error']}")

    return r.get("task_id", "")


def generate_audio(notebook_id: str, instructions: str = "",
                   timeout: int = 1200) -> str:
    """Generate podcast audio."""
    cmd = ["generate", "audio", "-n", notebook_id, "--json"]
    if instructions:
        cmd += [instructions]

    r = _run(*cmd, timeout=timeout)
    if "error" in r:
        raise RuntimeError(f"Generate audio gagal: {r['error']}")
    return r.get("task_id", "")


def artifact_wait(notebook_id: str, artifact_id: str,
                  timeout: int = 1200) -> str:
    """Tunggu artifact selesai."""
    r = _run("artifact", "wait", artifact_id, "-n", notebook_id,
             "--json", timeout=timeout)
    if "error" in r:
        return f"Gagal: {r['error']}"
    return "Artifact selesai."


def download_report(notebook_id: str, artifact_id: str,
                    output_path: str) -> str:
    """Download report ke file."""
    r = _run("download", "report", output_path, "-a", artifact_id,
             "-n", notebook_id)
    if r.get("returncode", 0) != 0:
        return f"Gagal download: {r.get('error', 'unknown')}"
    return f"Report tersimpan di {output_path}"


def download_audio(notebook_id: str, artifact_id: str,
                   output_path: str) -> str:
    """Download audio ke file."""
    r = _run("download", "audio", output_path, "-a", artifact_id,
             "-n", notebook_id)
    if r.get("returncode", 0) != 0:
        return f"Gagal download: {r.get('error', 'unknown')}"
    return f"Audio tersimpan di {output_path}"


# ── Convenience ────────────────────────────────────────────────────────────────

class Research:
    """
    NotebookLM Research Tool untuk Pi Agent.

    Usage:
        r = Research()
        nb = r.create("Riset SLM")
        r.add_url(nb, "https://huggingface.co/...")
        r.add_file(nb, "/path/to/doc.pdf")
        result = r.deep(nb, "Best SLM models for tool calling")
        answer = r.ask(nb, "Apa kesimpulan dari riset ini?")
    """

    def __init__(self):
        pass

    # ── Notebook ──────────────────────────────────────────────────────────────

    def create(self, title: str) -> str:
        """Buat notebook baru."""
        nb = create_notebook(title)
        print(f"✅ Notebook dibuat: {title}")
        return nb

    def list(self) -> list[dict]:
        """List semua notebook."""
        return list_notebooks()

    def delete(self, notebook_id: str):
        """Hapus notebook."""
        delete_notebook(notebook_id)
        print(f"✅ Notebook {notebook_id[:8]} dihapus")

    # ── Sources ───────────────────────────────────────────────────────────────

    def add_url(self, notebook_id: str, url: str) -> str:
        """Tambah URL source."""
        sid = add_url_source(notebook_id, url)
        print(f"✅ Source ditambahkan: {url}")
        return sid

    def add_file(self, notebook_id: str, filepath: str) -> str:
        """Tambah file source."""
        sid = add_file_source(notebook_id, filepath)
        print(f"✅ File ditambahkan: {filepath}")
        return sid

    def sources(self, notebook_id: str) -> list[dict]:
        """List semua source."""
        return list_sources(notebook_id)

    # ── Research ──────────────────────────────────────────────────────────────

    def fast(self, notebook_id: str, query: str) -> list[dict]:
        """Research cepat (fast mode)."""
        print(f"🔍 Fast research: {query[:60]}...")
        result = research_fast(notebook_id, query)
        print(f"✅ Fast research selesai")
        return result

    def deep(self, notebook_id: str, query: str,
             background: bool = False) -> str:
        """
        Research mendalam.

        Args:
            notebook_id: ID notebook
            query: pertanyaan riset
            background: True = non-blocking (return task ID)

        Returns:
            Jika background=True: task ID
            Jika background=False: jumlah source terimport
        """
        print(f"🔍 Deep research: {query[:60]}...")
        result = research_deep(notebook_id, query, wait=not background)
        if background:
            print(f"⏳ Research berjalan di background. Poll ID: {result[:16]}...")
        else:
            print(f"✅ {result}")
        return result

    def wait(self, notebook_id: str, timeout: int = 1800) -> str:
        """Tunggu research selesai."""
        return research_wait(notebook_id, timeout)

    # ── Query ─────────────────────────────────────────────────────────────────

    def ask(self, notebook_id: str, question: str) -> str:
        """Tanya isi notebook."""
        return ask(notebook_id, question)

    def query(self, notebook_id: str, question: str) -> dict:
        """Tanya dengan referensi."""
        return ask_with_refs(notebook_id, question)

    # ── Generate ──────────────────────────────────────────────────────────────

    def report(self, notebook_id: str, fmt: str = "briefing-doc",
               append: str = "") -> str:
        """Generate report."""
        print(f"📄 Generate {fmt}...")
        aid = generate_report(notebook_id, fmt, append)
        print(f"⏳ Report generation started. Artifact ID: {aid[:16]}...")
        return aid

    def podcast(self, notebook_id: str, instructions: str = "") -> str:
        """Generate podcast audio."""
        print(f"🎙 Generate podcast...")
        aid = generate_audio(notebook_id, instructions)
        print(f"⏳ Podcast generation started. Artifact ID: {aid[:16]}...")
        return aid

    def wait_artifact(self, notebook_id: str, artifact_id: str,
                      timeout: int = 1200) -> str:
        """Tunggu artifact selesai."""
        return artifact_wait(notebook_id, artifact_id, timeout)

    def download(self, notebook_id: str, artifact_id: str,
                 output_path: str, artifact_type: str = "report") -> str:
        """Download artifact."""
        if artifact_type == "report":
            return download_report(notebook_id, artifact_id, output_path)
        elif artifact_type == "audio":
            return download_audio(notebook_id, artifact_id, output_path)
        else:
            return f"Tipe {artifact_type} belum didukung"


# ── CLI Test ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NotebookLM Research Tool")
    parser.add_argument("action", choices=["list", "create", "ask", "search"])
    parser.add_argument("--title", "-t", help="Judul notebook")
    parser.add_argument("--query", "-q", help="Query riset")
    parser.add_argument("--notebook", "-n", help="ID notebook")
    parser.add_argument("--mode", choices=["fast", "deep"], default="fast")
    parser.add_argument("--background", action="store_true")

    args = parser.parse_args()
    r = Research()

    if args.action == "list":
        nbs = r.list()
        for nb in nbs:
            print(f"  {nb.get('id','?')[:8]}  {nb.get('title','?')}")
        print(f"Total: {len(nbs)} notebooks")

    elif args.action == "create":
        if not args.title:
            print("Error: --title required")
            sys.exit(1)
        nb = r.create(args.title)
        print(f"ID: {nb}")

    elif args.action == "ask":
        if not args.notebook or not args.query:
            print("Error: --notebook and --query required")
            sys.exit(1)
        answer = r.ask(args.notebook, args.query)
        print(answer)

    elif args.action == "search":
        if not args.notebook or not args.query:
            print("Error: --notebook and --query required")
            sys.exit(1)
        if args.mode == "fast":
            r.fast(args.notebook, args.query)
        else:
            r.deep(args.notebook, args.query, background=args.background)
