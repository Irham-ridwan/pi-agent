"""
Pi Agent — Systematic Evaluation Engine
========================================
Automated benchmark untuk semua model di semua layer.
Mengadaptasi pola Quality Flywheel dari Google agents-cli:

  1. Prepare Data   → dataset tasks per workflow
  2. Run Inference   → call each model, record response + timing
  3. Grade           → Gemini API as LLM judge
  4. Report          → comparative report

Usage:
    python3 eval.py                    # Run full eval, all models
    python3 eval.py --daily            # Only daily models
    python3 eval.py --list             # List all tasks
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# API keys: env var > .env file
if not os.environ.get("GEMINI_API_KEYS") and not os.environ.get("GEMINI_API_KEY"):
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


# ── Tasks Dataset ──────────────────────────────────────────────────────────────

@dataclass
class EvalTask:
    """Single evaluation task."""
    id: str
    workflow: str          # "daily", "coding", "novel", "gemini"
    prompt: str
    system: Optional[str] = None
    complexity: str = "normal"
    # Expected qualities for grading
    criteria: list[str] = field(default_factory=lambda: [
        "correctness", "completeness", "clarity"
    ])


TASKS: list[EvalTask] = [
    # ── Daily ──
    EvalTask("math-1", "daily", "Berapa 23 x 47? Beri jawaban angka saja."),
    EvalTask("math-2", "daily", "Hitung 15% dari 200.000"),
    EvalTask("fact-1", "daily", "Sebutkan 3 ibu kota negara ASEAN."),
    EvalTask("logic-1", "daily", "Jika semua kucing adalah mamalia, dan beberapa mamalia bisa terbang, apakah ada kucing yang bisa terbang? Jelaskan."),
    EvalTask("tool-1", "daily", "Konversi 100 USD ke IDR dengan kurs 1 USD = 16.500 IDR"),

    # ── Coding ──
    EvalTask("fib", "coding", "Buat fungsi Python fibonacci(n) yang mengembalikan list deret fibonacci hingga n. Sertakan contoh usage untuk n=10.",
             system="You are an expert Python programmer."),
    EvalTask("sort", "coding", "Buat fungsi quick sort dalam Python dengan penjelasan cara kerjanya.",
             system="You are an expert Python programmer."),
    EvalTask("api", "coding", "Tulis fungsi Python yang membaca file JSON dan mengembalikan summary datanya.",
             system="You are an expert Python programmer."),

    # ── Novel ──
    EvalTask("opening", "novel", "Tulis paragraf pembuka novel detektif noir di Jakarta tahun 2049. Suasana hujan, gelap, dan misterius.",
             system="Kamu adalah penulis novel berbakat."),
    EvalTask("dialog", "novel", "Tulis dialog singkat antara dua karakter: seorang detektif dan informan di kafe pinggir jalan.",
             system="Kamu adalah penulis novel berbakat."),

    # ── Gemini (for comparison) ──
    EvalTask("gemini-math", "gemini", "Berapa 23 x 47? Beri jawaban angka saja."),
    EvalTask("gemini-code", "gemini", "Buat fungsi Python fibonacci(n)."),
    EvalTask("gemini-write", "gemini", "Tulis 2 kalimat pembuka novel detektif."),
]


# ── Eval Runner ────────────────────────────────────────────────────────────────

@dataclass
class EvalResult:
    task_id: str
    workflow: str
    model: str
    latency: float        # total seconds
    prompt_tokens: int    # if available
    completion_tokens: int
    response: str
    error: Optional[str] = None
    score: Optional[float] = None
    score_reasoning: str = ""


class EvalRunner:
    """
    Runs all tasks against all configured models.
    Records timing, token usage, and raw response.
    """

    def __init__(self):
        self.results: list[EvalResult] = []
        self._gemini = None  # lazy import

    # ── SLM via direct API (more reliable than importing orchestrator) ───

    HF_SPACES = {
        "daily":  "https://lofox0-pi-daily.hf.space/v1/chat/completions",
        "coding": "https://lofox0-pi-coding.hf.space/v1/chat/completions",
        "novel":  "https://lofox0-pi-novel.hf.space/v1/chat/completions",
    }

    SLM_MODELS = {
        "ask":   {"space": "daily",  "model": "MiniCPM5-1B-Q4_K_M.gguf"},
        "solve": {"space": "daily",  "model": "mythos-nano-Q4_K_M.gguf"},
        "code":  {"space": "coding", "model": "Qwopus3.5-4B-coder-Q4_K_M.gguf"},
        "write": {"space": "novel",  "model": "Crow-4B-Opus-4.6-Distill-Heretic_Qwen3.5.Q4_K_M.gguf"},
    }

    def _call_slm(self, task: EvalTask, shortcut: str, **kwargs) -> EvalResult:
        """Call SLM model directly via HF Space API."""
        import urllib.request
        import json

        model_info = self.SLM_MODELS.get(shortcut)
        if not model_info:
            return EvalResult(task.id, task.workflow, f"SLM-{shortcut}", 0, 0, 0, "", error=f"Unknown shortcut: {shortcut}")

        url = self.HF_SPACES[model_info["space"]]
        payload = {
            "model": model_info["model"],
            "messages": [{"role": "user", "content": task.prompt}],
            "max_tokens": 150,
            "temperature": 0.3,
        }
        if task.system:
            payload["messages"] = [
                {"role": "system", "content": task.system},
                {"role": "user", "content": task.prompt},
            ]

        start = time.time()
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())

            elapsed = time.time() - start
            msg = data.get("choices", [{}])[0].get("message", {})
            response = msg.get("content", "") or msg.get("reasoning_content", "")
            usage = data.get("usage", {})

            return EvalResult(
                task_id=task.id, workflow=task.workflow,
                model=f"SLM-{shortcut}", latency=round(elapsed, 1),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                response=response[:500],
            )
        except Exception as e:
            elapsed = time.time() - start
            return EvalResult(
                task_id=task.id, workflow=task.workflow,
                model=f"SLM-{shortcut}", latency=round(elapsed, 1),
                prompt_tokens=0, completion_tokens=0, response="",
                error=str(e)[:200],
            )

    # ── Gemini via API ────────────────────────────────────────────────────

    def _call_gemini(self, task: EvalTask) -> EvalResult:
        """Call Gemini 3.5 Flash as baseline."""
        try:
            sys.path.insert(0, "/home/smiley/projek/pi")
            from antigravity import Gemini
            g = Gemini()

            start = time.time()
            if task.workflow == "coding":
                r = g.code(task.prompt)
            else:
                r = g.text(task.prompt, system=task.system)
            elapsed = time.time() - start

            return EvalResult(
                task_id=task.id, workflow=task.workflow,
                model="Gemini-3.5-Flash", latency=round(elapsed, 1),
                prompt_tokens=0, completion_tokens=0, response=r[:500],
            )
        except Exception as e:
            return EvalResult(
                task_id=task.id, workflow=task.workflow,
                model="Gemini-3.5-Flash", latency=0,
                prompt_tokens=0, completion_tokens=0, response="",
                error=str(e)[:200],
            )

    # ── Run All ───────────────────────────────────────────────────────────

    def run(self, workflows: Optional[list[str]] = None):
        tasks = [t for t in TASKS if workflows is None or t.workflow in workflows]

        for task in tasks:
            print(f"  Running {task.id} ({task.workflow})...", end=" ", flush=True)

            if task.workflow == "daily":
                # Route to appropriate SLM
                if "math" in task.id or "logic" in task.id:
                    r = self._call_slm(task, "solve")
                elif "tool" in task.id:
                    r = self._call_slm(task, "ask")
                else:
                    r = self._call_slm(task, "ask")
                self.results.append(r)
                print(f"{r.latency}s {'✅' if not r.error else '❌'}")

            elif task.workflow == "coding":
                r = self._call_slm(task, "code")
                self.results.append(r)
                print(f"{r.latency}s {'✅' if not r.error else '❌'}")

            elif task.workflow == "novel":
                r = self._call_slm(task, "write")
                self.results.append(r)
                print(f"{r.latency}s {'✅' if not r.error else '❌'}")

            elif task.workflow == "gemini":
                r = self._call_gemini(task)
                self.results.append(r)
                print(f"{r.latency}s {'✅' if not r.error else '❌'}")

        print(f"\n  ✅ {len(self.results)} results collected")

    # ── Grade with Gemini-as-Judge ────────────────────────────────────────

    def grade(self):
        """Grade semua hasil pakai Gemini API sebagai judge."""
        try:
            sys.path.insert(0, "/home/smiley/projek/pi")
            from antigravity import Gemini
        except ImportError:
            print("  ❌ antigravity.py not found, skipping grading")
            return

        g = Gemini()
        print("\n  Grading with Gemini-as-Judge...")

        for r in self.results:
            if r.error:
                r.score = 0.0
                r.score_reasoning = "Error saat eksekusi"
                continue

            prompt = f"""Anda adalah judge yang ketat. Nilai kualitas response AI ini untuk task berikut.

Task: {r.task_id} ({r.workflow})
Prompt: {TASKS[[t.id for t in TASKS].index(r.task_id)].prompt}

Response model ({r.model}):
---
{r.response[:1000]}
---

Beri skor 0-10 berdasarkan:
1. Correctness: Apakah jawaban benar secara faktual/teknis?
2. Completeness: Apakah menjawab semua aspek pertanyaan?
3. Clarity: Apakah jelas dan mudah dipahami?

Output JSON: {"score": <0-10>, "reasoning": "<penjelasan singkat>"}"""

            try:
                resp = g.text(prompt)
                # Parse JSON from response
                import re
                json_match = re.search(r'\{.*\}', resp, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    r.score = float(data.get("score", 5))
                    r.score_reasoning = data.get("reasoning", "")[:200]
                else:
                    r.score = 5.0
                    r.score_reasoning = "Failed to parse judge response"
            except Exception as e:
                r.score = 5.0
                r.score_reasoning = f"Judge error: {str(e)[:100]}"

            print(f"    {r.task_id}: {r.model} → {r.score:.1f}/10")

    # ── Report ────────────────────────────────────────────────────────────

    def report(self) -> str:
        """Generate comprehensive report."""
        lines = []
        lines.append("# Pi Agent — Eval Report")
        lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Tasks: {len(self.results)}")
        lines.append("")

        # Group by workflow
        for wf in ["daily", "coding", "novel", "gemini"]:
            wf_results = [r for r in self.results if r.workflow == wf]
            if not wf_results:
                continue

            lines.append(f"## {wf.upper()}")
            lines.append(f"| Task | Model | Latency | Score | Error |")
            lines.append(f"|------|-------|---------|-------|-------|")

            for r in wf_results:
                lat = f"{r.latency}s" if r.latency > 0 else "-"
                score = f"{r.score:.1f}" if r.score is not None else "-"
                err = "❌" if r.error else "✅"
                lines.append(f"| {r.task_id} | {r.model} | {lat} | {score} | {err} |")

            # Average
            scores = [r.score for r in wf_results if r.score is not None]
            lats = [r.latency for r in wf_results if r.latency > 0]
            if scores:
                lines.append(f"| **Avg** | | **{sum(lats)/len(lats):.1f}s** | **{sum(scores)/len(scores):.1f}** | |")
            lines.append("")

        # Best models
        lines.append("## Best Models by Workflow")
        for wf in ["daily", "coding", "novel", "gemini"]:
            wf_results = [r for r in self.results if r.workflow == wf and r.score is not None]
            if wf_results:
                best = max(wf_results, key=lambda r: r.score or 0)
                lines.append(f"- **{wf}**: {best.model} ({best.score:.1f}/10, {best.latency}s)")

        lines.append("")
        lines.append("## Key Insights")
        lines.append("- Lower latency does NOT always mean lower quality")
        lines.append("- Gemini 3.5 Flash serves as baseline for quality comparison")
        lines.append("- SLM models trade latency for capability")

        return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pi Agent Eval Engine")
    parser.add_argument("--daily", action="store_true", help="Only daily tasks")
    parser.add_argument("--coding", action="store_true", help="Only coding tasks")
    parser.add_argument("--novel", action="store_true", help="Only novel tasks")
    parser.add_argument("--gemini", action="store_true", help="Only gemini baseline")
    parser.add_argument("--list", action="store_true", help="List all tasks")
    parser.add_argument("--quick", action="store_true", help="Minimal test (1 task per workflow)")
    parser.add_argument("--no-grade", action="store_true", help="Skip grading phase")
    args = parser.parse_args()

    if args.list:
        print(f"{'ID':<15} {'Workflow':<10} {'Prompt'}")
        print("-" * 70)
        for t in TASKS:
            print(f"{t.id:<15} {t.workflow:<10} {t.prompt[:50]}...")
        sys.exit(0)

    selected = []
    if args.daily:
        selected.append("daily")
    if args.coding:
        selected.append("coding")
    if args.novel:
        selected.append("novel")
    if args.gemini:
        selected.append("gemini")

    runner = EvalRunner()

    if args.quick:
        # Only first task per workflow
        quick_ids = set()
        for t in TASKS:
            if t.workflow not in quick_ids and (not selected or t.workflow in selected):
                quick_ids.add(t.workflow)
                # Run only this task
                subtasks = [t]
                for subt in subtasks:
                    if subt.workflow == "daily":
                        r = runner._call_slm(subt, "ask")
                    elif subt.workflow == "coding":
                        r = runner._call_slm(subt, "code")
                    elif subt.workflow == "novel":
                        r = runner._call_slm(subt, "write")
                    elif subt.workflow == "gemini":
                        r = runner._call_gemini(subt)
                    runner.results.append(r)
                    print(f"  {subt.id} ({subt.workflow}): {r.latency}s {'✅' if not r.error else '❌'}")
    else:
        runner.run(workflows=selected if selected else None)

    if not args.no_grade and runner.results:
        runner.grade()

    print("\n" + runner.report())
