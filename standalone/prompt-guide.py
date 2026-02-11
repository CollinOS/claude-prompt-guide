#!/usr/bin/env python3
"""
Claude Prompt Guide — Standalone Version
=========================================
Single-file version with zero required dependencies.
Drop into ~/.claude/hooks/ and use directly.

Usage:
  python prompt-guide.py "fix the auth bug"
  python prompt-guide.py
"""

import sys
import os
import json
import re
import subprocess
import shutil
import argparse

# ── Optional rich ─────────────────────────────────────────────────────

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.rule import Rule
    _console = Console(stderr=True)
    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False


def _strip(t):
    return re.sub(r"\[.*?\]", "", t)

def show(m):
    if _HAS_RICH: _console.print(m)
    else: print(_strip(m), file=sys.stderr)

def show_panel(t, title="", border="blue"):
    if _HAS_RICH: _console.print(Panel(f"[bold]{t}[/bold]", title=title, border_style=border))
    else: print(f"\n--- {title} ---\n{t}\n---\n", file=sys.stderr)

def ask(default=""):
    if _HAS_RICH: return Prompt.ask("  [bold]>[/bold]", default=default, console=_console)
    try:
        r = input("  > ").strip()
        return r if r else default
    except EOFError:
        return default

def ask_choice(p, choices, default="yes"):
    if _HAS_RICH: return Prompt.ask(f"[bold]{p}[/bold]", choices=choices, default=default, console=_console)
    r = input(f"{p} [{'/'.join(choices)}] ({default}): ").strip()
    return r if r in choices else default


# ── Claude CLI ────────────────────────────────────────────────────────

def _find_claude():
    f = shutil.which("claude")
    if f: return f
    for p in ["~/.claude/local/claude", "/usr/local/bin/claude"]:
        e = os.path.expanduser(p)
        if os.path.isfile(e): return e
    return None

def call_claude(prompt, system="", timeout=30):
    cb = _find_claude()
    if not cb:
        print("Error: claude CLI not found. Is Claude Code installed?", file=sys.stderr)
        sys.exit(1)
    cmd = [cb, "--print", "--output-format", "text"]
    if system: cmd.extend(["--system-prompt", system])
    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


# ── Prompts ───────────────────────────────────────────────────────────

ANALYZER = """You are an expert at helping people write effective prompts for AI coding agents.

You will receive a draft prompt for Claude Code (an agentic coding assistant in a terminal).

Identify the 2-4 most important pieces of missing context. Only ask about genuinely unclear things.

Think like a senior dev: What would you need to know before starting?

Rules:
- 2-4 questions max. 0 if already great.
- Specific to THIS prompt, not generic.
- Quick to answer (one sentence).
- Don't ask what the agent can discover itself.

Respond with ONLY this JSON:
{"task_summary":"...","questions":[{"question":"...","why":"...","example_answer":"..."}]}"""

ASSEMBLER = """Combine the original prompt with additional context into a single clean prompt for Claude Code. Preserve original intent. Weave context naturally. Keep it concise. Don't add fluff or steps the user didn't ask for. Output ONLY the final prompt."""


# ── Logic ─────────────────────────────────────────────────────────────

def parse_json(raw):
    c = raw.replace("```json","").replace("```","").strip()
    try: return json.loads(c)
    except json.JSONDecodeError: pass
    s, e = c.find("{"), c.rfind("}")+1
    if s >= 0 and e > s:
        try: return json.loads(c[s:e])
        except json.JSONDecodeError: pass
    return {}

def analyze(prompt):
    r = call_claude(f"Analyze this prompt:\n\n{prompt}", ANALYZER)
    return parse_json(r) if r else {"task_summary":"","questions":[]}

def assemble(original, answers):
    filled = {q:a for q,a in answers.items() if a.strip()}
    if not filled: return original
    ctx = "\n\n".join(f"Q: {q}\nA: {a}" for q,a in filled.items())
    r = call_claude(f"Original prompt:\n{original}\n\nAdditional context:\n{ctx}", ASSEMBLER)
    return r if r else original

def run(raw):
    show("")
    show_panel(raw, title="Your prompt")
    show("\n[dim]Thinking...[/dim]")
    a = analyze(raw)
    s = a.get("task_summary","")
    qs = a.get("questions",[])
    if s: show(f"\n[dim]Understanding:[/dim] {s}")
    if not qs:
        show("\n[green]Prompt looks detailed enough.[/green]\n")
        return raw
    n = len(qs)
    show(f"\n[dim]{n} quick question{'s' if n!=1 else ''} (enter to skip):[/dim]\n")
    answers = {}
    for i,q in enumerate(qs,1):
        show(f"  [bold yellow]{i}.[/bold yellow] {q['question']}")
        if q.get("why"): show(f"     [dim italic]{q['why']}[/dim italic]")
        if q.get("example_answer"): show(f"     [dim]e.g. {q['example_answer']}[/dim]")
        answers[q["question"]] = ask("")
        show("")
    if not any(v.strip() for v in answers.values()):
        show("[dim]No context added. Using original.[/dim]\n")
        return raw
    show("[dim]Assembling...[/dim]")
    final = assemble(raw, answers)
    if _HAS_RICH: _console.print(Rule("Assembled Prompt", style="green"))
    show_panel(final, title="Final Prompt", border="green")
    show("")
    c = ask_choice("Send to Claude?", ["yes","edit","cancel"], "yes")
    if c == "yes": return final
    elif c == "edit":
        show("[dim]Type edited prompt (Ctrl+D to finish):[/dim]")
        lines = []
        try:
            while True: lines.append(input())
        except EOFError: pass
        return "\n".join(lines) if lines else final
    else: sys.exit(0)

def main():
    p = argparse.ArgumentParser(description="Guided prompt builder for Claude Code")
    p.add_argument("prompt", nargs="?")
    p.add_argument("-q","--quiet", action="store_true")
    a = p.parse_args()
    if a.prompt: raw = a.prompt
    elif not sys.stdin.isatty(): raw = sys.stdin.read().strip()
    else:
        show("\n[bold]What do you want Claude Code to do?[/bold]")
        raw = ask("")
    if not raw:
        print("Error: No prompt.", file=sys.stderr)
        sys.exit(1)
    print(run(raw))

if __name__ == "__main__":
    main()