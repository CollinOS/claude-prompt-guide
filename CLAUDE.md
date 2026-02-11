
## Project: Claude Prompt Guide

An interactive CLI tool that coaches users into writing better prompts for Claude Code by asking targeted follow-up questions before the prompt is sent.

### Architecture

This is a Python CLI tool with two distribution modes:

1. **Package mode** (`prompt_guide/`): The structured source code, useful for development and if pip distribution is added later. Entry point is `prompt_guide.cli:main`.
2. **Standalone mode** (`standalone/prompt-guide.py`): The primary distribution file. A single self-contained Python file users drop into `~/.claude/scripts/`. Has zero required dependencies — `rich` is optional for nicer UI, falls back to plain stdin/stdout. This is what most users will install.

The primary usage method is as a **Claude Code slash command** (`/guide`). Users create a `~/.claude/commands/guide.md` file that tells Claude Code to run our script. This is NOT a toggle — it runs per-prompt when the user explicitly types `/guide`. There is no persistent mode or PreMessage hook (yet).

### Key Design Decisions

- **No API key required.** The tool calls the `claude` CLI binary via subprocess in `--print` mode, so it uses whatever auth Claude Code already has (API key or Max subscription). This is handled in `claude_cli.py`. Do NOT add direct Anthropic API calls — the whole point is zero extra auth.
- **Dynamic questions, not hardcoded.** Instead of a static question bank, we send the user's prompt to Claude and ask it to generate 2-4 follow-up questions specific to that prompt. The system prompts for this are in `prompts.py`.
- **Guide, don't rewrite.** The tool asks the user questions and assembles their answers with the original prompt. It does NOT silently rewrite prompts. The user always sees and approves what gets sent. This is a core philosophy — don't change it.
- **UI goes to stderr, final prompt goes to stdout.** This allows piping: `claude "$(prompt-guide -q 'fix bug')"`. All interactive UI (questions, panels, status) must write to stderr. Only the final assembled prompt goes to stdout.

### File Overview

```
prompt_guide/
  __init__.py      - Version string only
  __main__.py      - Enables `python -m prompt_guide`
  cli.py           - Main entry point, argument parsing, interactive flow
  prompts.py       - System prompts for the analyzer and assembler calls
  claude_cli.py    - Wrapper around the `claude` CLI binary (subprocess calls)
standalone/
  prompt-guide.py  - Self-contained single file combining all of the above
```

### How the Flow Works

1. User provides a draft prompt (arg, stdin, or interactive)
2. `cli.py:run()` calls `claude_cli.py:call_claude()` with the analyzer system prompt
3. Claude returns JSON with `task_summary` and `questions` array
4. Tool asks the user each question interactively (skippable)
5. `cli.py:assemble()` calls Claude again to combine original prompt + answers
6. User reviews assembled prompt and chooses send/edit/cancel
7. Final prompt printed to stdout

### Working on This Project

**To test changes:**
```bash
# Install in dev mode
pip install -e .

# Run directly
python -m prompt_guide "test prompt here"

# Run standalone version
python standalone/prompt-guide.py "test prompt here"
```

**Important constraints:**
- The standalone file must remain self-contained — no imports from the package. If you change logic in the package, sync it to standalone.
- `rich` must remain optional everywhere. Always wrap rich imports in try/except with plain fallbacks.
- Keep subprocess calls to claude CLI simple. Use `--print` and `--output-format text`. Don't rely on undocumented flags.
- JSON parsing from Claude responses must be defensive. Claude sometimes wraps JSON in markdown fences or adds preamble. Always strip and handle failures.

**Known limitations / future work:**
- No `PreMessage` hook in Claude Code yet — when one ships, add support so this runs automatically instead of requiring `/guide` or the shell alias.
- The `claude --print --system-prompt` flags should be verified against the current Claude Code CLI docs. Flag names may change across versions.
- No tests yet. Priority: test JSON parsing edge cases, test fallback behavior without rich, test behavior when claude CLI is missing.
- Could add a `--local` flag to use Ollama instead of Claude CLI for the analysis step (zero API usage).
- Could add learning/adaptation: track which questions users always skip and stop asking them.
- The assembler step could be replaced with simple string concatenation to save an API call. Worth A/B testing quality vs latency.
- Not currently published to PyPI. If that changes, pyproject.toml is already configured for it — just needs `hatch build && hatch publish`.
- The `/guide` slash command is per-use, not a toggle. If Claude Code adds a `PreMessage` hook in the future, we could offer a persistent mode.

### Style

- Python 3.9+ compatible
- No type checking configured yet but type hints are welcome
- Keep the codebase small — this should stay a focused, lightweight tool
