"""Wrapper around the Claude Code CLI binary."""

import os
import shutil
import subprocess
import sys


def find_claude_cli() -> str | None:
    """Locate the claude CLI binary."""
    found = shutil.which("claude")
    if found:
        return found
    for path in ["~/.claude/local/claude", "/usr/local/bin/claude"]:
        expanded = os.path.expanduser(path)
        if os.path.isfile(expanded):
            return expanded
    return None


def call_claude(prompt: str, system: str = "", timeout: int = 30) -> str:
    """
    Call the claude CLI in print mode (non-interactive, single response).
    Uses whatever auth the user already has configured for Claude Code.

    Args:
        prompt: The prompt to send.
        system: Optional system prompt.
        timeout: Seconds before giving up.

    Returns:
        Claude's response text, or empty string on failure.
    """
    claude_bin = find_claude_cli()
    if not claude_bin:
        print(
            "Error: claude CLI not found. Is Claude Code installed?\n"
            "Install: https://docs.anthropic.com/en/docs/claude-code",
            file=sys.stderr,
        )
        sys.exit(1)

    cmd = [claude_bin, "--print", "--output-format", "text"]

    if system:
        cmd.extend(["--system-prompt", system])

    # Pass prompt via stdin to avoid shell escaping issues
    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            print(f"Claude CLI error: {result.stderr.strip()}", file=sys.stderr)
            return ""
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print("Claude CLI timed out.", file=sys.stderr)
        return ""
    except FileNotFoundError:
        print("Could not run claude CLI.", file=sys.stderr)
        return ""
