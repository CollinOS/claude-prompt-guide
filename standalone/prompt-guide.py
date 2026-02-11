#!/usr/bin/env python3
"""
Claude Prompt Guide — Standalone Version
=========================================
Single-file version with zero required dependencies.
Drop into ~/.claude/scripts/ and use via a slash command.

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


# Only strip Rich-style markup tags like [bold], [dim], [/bold], [green],
# [bold yellow], etc. — not arbitrary square-bracket content like array[0].
_RICH_TAG_RE = re.compile(r"\[/?[a-zA-Z]\w*(?:\s+\w+)*\]")

def _strip(t):
    return _RICH_TAG_RE.sub("", t)

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
    try:
        r = input(f"{p} [{'/'.join(choices)}] ({default}): ").strip()
        return r if r in choices else default
    except EOFError:
        return default


# ── Claude CLI ────────────────────────────────────────────────────────

class ClaudeNotFoundError(RuntimeError):
    pass

_cached_claude_bin = None

def _find_claude():
    global _cached_claude_bin
    if _cached_claude_bin is not None:
        return _cached_claude_bin
    f = shutil.which("claude")
    if f:
        _cached_claude_bin = f
        return f
    for p in ["~/.claude/local/claude", "/usr/local/bin/claude"]:
        e = os.path.expanduser(p)
        if os.path.isfile(e):
            _cached_claude_bin = e
            return e
    return None

def call_claude(prompt, system="", timeout=60):
    cb = _find_claude()
    if not cb:
        raise ClaudeNotFoundError(
            "claude CLI not found. Is Claude Code installed?\n"
            "Install: https://docs.anthropic.com/en/docs/claude-code"
        )
    cmd = [cb, "--print", "--output-format", "text"]
    if system: cmd.extend(["--system-prompt", system])
    try:
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout)
        if r.returncode != 0:
            print(f"Claude CLI error: {r.stderr.strip()}", file=sys.stderr)
            return ""
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        print("Claude CLI timed out.", file=sys.stderr)
        return ""
    except FileNotFoundError:
        print("Could not run claude CLI.", file=sys.stderr)
        return ""


# ── Prompts ───────────────────────────────────────────────────────────

ANALYZER = (
    "You are an expert at helping people write effective prompts for AI coding agents.\n"
    "\n"
    "You will receive a draft prompt that someone is about to send to Claude Code (an agentic "
    "coding assistant that works in a terminal, can read/write files, run commands, and make "
    "changes to a codebase).\n"
    "\n"
    "Your job: identify the 2-4 most important pieces of missing context that would help "
    "Claude Code do a significantly better job. Only ask about things that are genuinely "
    "unclear or missing — if the prompt is already detailed enough on a topic, don't ask "
    "about it.\n"
    "\n"
    "Think about what a senior developer would want to know before starting this task:\n"
    "- What specific behavior is expected vs what's happening?\n"
    "- Which part of the codebase is involved?\n"
    "- Are there constraints, dependencies, or things that shouldn't be touched?\n"
    "- What does 'done' look like?\n"
    "- Is there relevant context the person probably knows but didn't mention?\n"
    "\n"
    "Rules:\n"
    "- Generate 2-4 questions. Not more. Fewer is fine if the prompt is already good.\n"
    "- Each question should be specific to THIS prompt, not generic.\n"
    "- If the prompt is already excellent and detailed, return 0 questions.\n"
    "- Questions should be quick to answer — aim for one-sentence responses.\n"
    "- Don't ask about things the coding agent can figure out on its own "
    "(like 'what language is the project in' — it can just look).\n"
    "- Don't ask about things that would be nice to know but won't meaningfully "
    "change the outcome.\n"
    "\n"
    "Respond with ONLY a JSON object in this exact format, no other text:\n"
    "{\n"
    '  "task_summary": "one-line description of what you understand the task to be",\n'
    '  "questions": [\n'
    "    {\n"
    '      "question": "the question to ask the user",\n'
    '      "why": "brief reason this matters (shown as hint)",\n'
    '      "example_answer": "a plausible example answer to guide the user"\n'
    "    }\n"
    "  ]\n"
    "}"
)

ASSEMBLER = (
    "You combine a user's original prompt with additional context they provided "
    "into a single clean, well-structured prompt for Claude Code.\n"
    "\n"
    "Rules:\n"
    "- Preserve the user's original intent and wording as the core.\n"
    "- Weave in the additional context naturally — don't just append it as a list.\n"
    "- Keep it concise. Don't add fluff, instructions about 'being careful', "
    "or things the user didn't say.\n"
    "- Don't add steps or structure the user didn't ask for. Just integrate the context.\n"
    "- The result should read like the user wrote it themselves, just more complete.\n"
    "- Output ONLY the final prompt text. No preamble, no explanation."
)


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

def _validate_questions(questions):
    valid = []
    for q in questions:
        if isinstance(q, dict) and isinstance(q.get("question"), str) and q["question"].strip():
            valid.append(q)
    return valid

def analyze(prompt):
    r = call_claude(f"Analyze this prompt:\n\n{prompt}", ANALYZER)
    if not r:
        return {"task_summary":"","questions":[]}
    result = parse_json(r)
    if not result:
        return {"task_summary":"","questions":[]}
    raw_questions = result.get("questions", [])
    if not isinstance(raw_questions, list):
        raw_questions = []
    result["questions"] = _validate_questions(raw_questions)
    return result

def assemble(original, answers):
    filled = {q:a for q,a in answers.items() if a.strip()}
    if not filled: return original
    ctx = "\n\n".join(f"Q: {q}\nA: {a}" for q,a in filled.items())
    r = call_claude(f"Original prompt:\n{original}\n\nAdditional context:\n{ctx}", ASSEMBLER)
    return r if r else original

def run(raw, quiet=False):
    if not quiet:
        show("")
        show_panel(raw, title="Your prompt")
        show("\n[dim]Thinking about what would help...[/dim]")

    a = analyze(raw)
    s = a.get("task_summary","")
    qs = a.get("questions",[])

    if not quiet and s:
        show(f"\n[dim]Understanding:[/dim] {s}")

    if not qs:
        if not quiet:
            show("\n[green]Prompt looks detailed enough — no extra questions needed.[/green]\n")
        return raw

    # In quiet mode, we can't ask questions interactively — return original
    if quiet:
        return raw

    n = len(qs)
    show(f"\n[dim]{n} quick question{'s' if n!=1 else ''} (enter to skip any):[/dim]\n")
    answers = {}
    for i,q in enumerate(qs,1):
        show(f"  [bold yellow]{i}.[/bold yellow] {q['question']}")
        if q.get("why"): show(f"     [dim italic]{q['why']}[/dim italic]")
        if q.get("example_answer"): show(f"     [dim]e.g. {q['example_answer']}[/dim]")
        answers[q["question"]] = ask("")
        show("")
    if not any(v.strip() for v in answers.values()):
        show("[dim]No extra context added. Using original prompt.[/dim]\n")
        return raw
    show("[dim]Assembling...[/dim]")
    final = assemble(raw, answers)
    if _HAS_RICH: _console.print(Rule("Assembled Prompt", style="green"))
    show_panel(final, title="Final Prompt", border="green")
    show("")
    c = ask_choice("Send to Claude?", ["yes","edit","cancel"], "yes")
    if c == "yes": return final
    elif c == "edit":
        show("[dim]Type your edited prompt (Ctrl+D to finish):[/dim]")
        lines = []
        try:
            while True: lines.append(input())
        except EOFError: pass
        return "\n".join(lines) if lines else final
    else: sys.exit(0)

def main():
    p = argparse.ArgumentParser(description="Guided prompt builder for Claude Code")
    p.add_argument("prompt", nargs="?")
    p.add_argument("-q","--quiet", action="store_true",
                   help="Output only the final prompt (for piping to claude)")
    a = p.parse_args()

    stdin_is_pipe = not sys.stdin.isatty()

    if a.prompt: raw = a.prompt
    elif stdin_is_pipe: raw = sys.stdin.read().strip()
    else:
        show("\n[bold]What do you want Claude Code to do?[/bold]")
        raw = ask("")
    if not raw:
        print("Error: No prompt provided.", file=sys.stderr)
        sys.exit(1)

    # Force quiet mode when stdin is piped — interactive Q&A can't work
    quiet = a.quiet or stdin_is_pipe

    try:
        print(run(raw, quiet=quiet))
    except ClaudeNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(130)

if __name__ == "__main__":
    main()
