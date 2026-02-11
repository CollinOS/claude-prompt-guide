"""Main CLI entry point and interactive flow."""

import argparse
import json
import re
import sys

from prompt_guide.claude_cli import call_claude, ClaudeNotFoundError
from prompt_guide.prompts import ANALYZER_SYSTEM, ASSEMBLER_SYSTEM

# ── Optional rich import ──────────────────────────────────────────────

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.rule import Rule

    console = Console(stderr=True)
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


# ── UI helpers (work with or without rich) ────────────────────────────

# Only strip Rich-style markup tags like [bold], [dim], [/bold], [green],
# [bold yellow], etc. — not arbitrary square-bracket content like array[0].
_RICH_TAG_RE = re.compile(
    r"\[/?[a-zA-Z]\w*(?:\s+\w+)*\]"
)


def _strip_markup(text: str) -> str:
    return _RICH_TAG_RE.sub("", text)


def show(msg: str):
    if HAS_RICH:
        console.print(msg)
    else:
        print(_strip_markup(msg), file=sys.stderr)


def show_panel(text: str, title: str = "", border: str = "blue"):
    if HAS_RICH:
        console.print(Panel(f"[bold]{text}[/bold]", title=title, border_style=border))
    else:
        print(f"\n--- {title} ---", file=sys.stderr)
        print(text, file=sys.stderr)
        print("---\n", file=sys.stderr)


def ask(default: str = "") -> str:
    if HAS_RICH:
        return Prompt.ask("  [bold]>[/bold]", default=default, console=console)
    else:
        try:
            result = input("  > ").strip()
            return result if result else default
        except EOFError:
            return default


def ask_choice(prompt_text: str, choices: list[str], default: str = "yes") -> str:
    if HAS_RICH:
        return Prompt.ask(
            f"[bold]{prompt_text}[/bold]",
            choices=choices,
            default=default,
            console=console,
        )
    else:
        try:
            raw = input(f"{prompt_text} [{'/'.join(choices)}] ({default}): ").strip()
            return raw if raw in choices else default
        except EOFError:
            return default


# ── Core logic ────────────────────────────────────────────────────────

def parse_json_response(raw: str) -> dict:
    """Defensively parse JSON from Claude's response."""
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to extract JSON object from surrounding text
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start:end])
            except json.JSONDecodeError:
                pass
    return {}


def _validate_questions(questions: list) -> list[dict]:
    """Filter questions list to only well-formed question dicts."""
    valid = []
    for q in questions:
        if isinstance(q, dict) and isinstance(q.get("question"), str) and q["question"].strip():
            valid.append(q)
    return valid


def analyze(raw_prompt: str) -> dict:
    """Ask Claude to analyze the prompt and generate follow-up questions."""
    response = call_claude(
        prompt=f"Analyze this prompt:\n\n{raw_prompt}",
        system=ANALYZER_SYSTEM,
    )
    if not response:
        return {"task_summary": "", "questions": []}

    result = parse_json_response(response)
    if not result:
        return {"task_summary": "", "questions": []}

    # Validate that questions is a list of well-formed dicts
    raw_questions = result.get("questions", [])
    if not isinstance(raw_questions, list):
        raw_questions = []
    result["questions"] = _validate_questions(raw_questions)

    return result


def assemble(original: str, answers: dict[str, str]) -> str:
    """Ask Claude to combine the original prompt with gathered context."""
    filled = {q: a for q, a in answers.items() if a.strip()}
    if not filled:
        return original

    context = "\n\n".join(f"Q: {q}\nA: {a}" for q, a in filled.items())

    response = call_claude(
        prompt=f"Original prompt:\n{original}\n\nAdditional context:\n{context}",
        system=ASSEMBLER_SYSTEM,
    )
    return response if response else original


def run(raw_prompt: str, quiet: bool = False) -> str:
    """Main interactive guide flow.

    Args:
        raw_prompt: The user's draft prompt.
        quiet: If True, skip interactive Q&A and auto-send the assembled prompt.
    """
    if not quiet:
        show("")
        show_panel(raw_prompt, title="Your prompt")
        show("\n[dim]Thinking about what would help...[/dim]")

    analysis = analyze(raw_prompt)

    summary = analysis.get("task_summary", "")
    questions = analysis.get("questions", [])

    if not quiet and summary:
        show(f"\n[dim]Understanding:[/dim] {summary}")

    if not questions:
        if not quiet:
            show("\n[green]Your prompt looks detailed enough — no extra questions needed.[/green]\n")
        return raw_prompt

    # In quiet mode, we can't ask questions interactively — return original
    if quiet:
        return raw_prompt

    count = len(questions)
    show(f"\n[dim]{count} quick question{'s' if count != 1 else ''} (enter to skip any):[/dim]\n")

    answers: dict[str, str] = {}
    for i, q in enumerate(questions, 1):
        show(f"  [bold yellow]{i}.[/bold yellow] {q['question']}")
        if q.get("why"):
            show(f"     [dim italic]{q['why']}[/dim italic]")
        if q.get("example_answer"):
            show(f"     [dim]e.g. {q['example_answer']}[/dim]")
        answers[q["question"]] = ask(default="")
        show("")

    if not any(v.strip() for v in answers.values()):
        show("[dim]No extra context added. Using original prompt.[/dim]\n")
        return raw_prompt

    show("[dim]Assembling...[/dim]")
    final = assemble(raw_prompt, answers)

    if HAS_RICH:
        console.print(Rule("Assembled Prompt", style="green"))
    show_panel(final, title="Final Prompt", border="green")
    show("")

    choice = ask_choice("Send to Claude?", ["yes", "edit", "cancel"], "yes")

    if choice == "yes":
        return final
    elif choice == "edit":
        show("[dim]Type your edited prompt (Ctrl+D to finish):[/dim]")
        lines = []
        try:
            while True:
                lines.append(input())
        except EOFError:
            pass
        return "\n".join(lines) if lines else final
    else:
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Guided prompt builder for Claude Code",
    )
    parser.add_argument("prompt", nargs="?", help="Your initial prompt")
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Output only the final prompt (for piping to claude)",
    )
    args = parser.parse_args()

    # Get prompt from arg, stdin, or interactive
    stdin_is_pipe = not sys.stdin.isatty()

    if args.prompt:
        raw = args.prompt
    elif stdin_is_pipe:
        raw = sys.stdin.read().strip()
    else:
        show("\n[bold]What do you want Claude Code to do?[/bold]")
        raw = ask(default="")

    if not raw:
        print("Error: No prompt provided.", file=sys.stderr)
        sys.exit(1)

    # Force quiet mode when stdin is piped — interactive Q&A can't work
    quiet = args.quiet or stdin_is_pipe

    try:
        final = run(raw, quiet=quiet)
        print(final)
    except ClaudeNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(130)
