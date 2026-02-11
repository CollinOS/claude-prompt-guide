
## Project: Claude Prompt Guide

An interactive CLI tool that coaches users into writing better prompts for Claude Code by asking targeted follow-up questions before the prompt is sent.

### Architecture

This is a Python CLI tool with two distribution modes:

1. **Package mode** (`prompt_guide/`): Installable via pip/pipx. Entry point is `prompt_guide.cli:main`, registered as the `prompt-guide` command in pyproject.toml.
2. **Standalone mode** (`standalone/prompt-guide.py`): A single self-contained Python file users can drop into `~/.claude/hooks/`. Has zero required dependencies — `rich` is optional for nicer UI, falls back to plain stdin/stdout.

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

### Style

- Python 3.9+ compatible
- No type checking configured yet but type hints are welcome
- Keep the codebase small — this should stay a focused, lightweight tool


# ═══════════════════════════════════════════════════════════════════════
# FILE: README.md
# ═══════════════════════════════════════════════════════════════════════

# Claude Prompt Guide

An interactive CLI tool that coaches you into writing better prompts for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Instead of rewriting your prompt for you, it asks the right follow-up questions so Claude Code gets the context it needs on the first try.

**No extra API key needed** — it uses your existing Claude Code authentication.

## Demo

```
$ prompt-guide "fix the auth bug"

┌─ Your prompt ────────────────────────────┐
│ fix the auth bug                         │
└──────────────────────────────────────────┘

Understanding: Fix a bug in the authentication system

3 quick questions to help Claude help you (enter to skip any):

  1. What error or behavior are users experiencing?
     Helps narrow down where the bug is
     e.g. users get a 403 after clicking the password reset link
  > users can't log in after changing their email

  2. Is this related to a recent change or deployment?
     Helps identify the cause
     e.g. started after last Friday's release
  > we just migrated the user table

  3. Specific files you suspect?
     Saves Claude from searching the whole codebase
  >

─── Assembled Prompt ──────────────────────
┌──────────────────────────────────────────┐
│ Fix the auth bug. Users can't log in     │
│ after changing their email. This likely  │
│ started after the recent user table      │
│ migration — check that the login flow    │
│ handles the new table schema correctly.  │
└──────────────────────────────────────────┘

Send to Claude? [yes/edit/cancel]: yes
```

## Install

### Option A: pip

```bash
pip install claude-prompt-guide
```

### Option B: pipx (recommended — keeps it isolated)

```bash
pipx install claude-prompt-guide
```

### Option C: Single file (no install needed)

```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/prompt-guide.py \
  https://raw.githubusercontent.com/yourname/claude-prompt-guide/main/standalone/prompt-guide.py
chmod +x ~/.claude/hooks/prompt-guide.py
```

### Option D: From source

```bash
git clone https://github.com/yourname/claude-prompt-guide.git
cd claude-prompt-guide
pip install .
```

### Optional: nicer UI

```bash
pip install rich
```

The tool works without `rich` — it falls back to plain text. Rich just makes it prettier.

## Prerequisites

- Python 3.9+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated

That's it. No API key to configure — the tool uses your existing Claude Code auth.

## Usage

### Standalone

```bash
# With a prompt
prompt-guide "add pagination to the users API"

# Interactive
prompt-guide

# Quiet mode — outputs only the final prompt
prompt-guide -q "fix the login bug"
```

### Piped into Claude Code

```bash
claude "$(prompt-guide -q 'fix the login bug')"
```

### Shell alias (recommended)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
cg() {
    local enriched
    enriched=$(prompt-guide -q "$1")
    if [ $? -eq 0 ] && [ -n "$enriched" ]; then
        claude "$enriched"
    fi
}
```

Then just:

```bash
cg "add dark mode"
```

### Single-file version

If you used the single-file install (Option C):

```bash
python3 ~/.claude/hooks/prompt-guide.py "fix the auth bug"
```

## How It Works

1. You type a casual prompt
2. The tool sends it to Claude (via the `claude` CLI) to identify what context is missing
3. It asks you 2-4 targeted follow-up questions specific to your task
4. You answer in a few words each (or skip any)
5. It assembles everything into a clean prompt
6. You review and send, edit, or cancel

The questions are generated dynamically — not from a static template. So they're always relevant to what you're actually asking.

## Why This Instead of a Prompt Rewriter?

Prompt rewriters change your words behind the scenes. This tool **asks you questions** instead. The difference:

- **You stay in control** of what gets sent
- **You learn** what context matters over time
- **Your intent** is never misinterpreted by a rewriter
- **The context** comes from you — the person who actually knows the codebase

After using this for a while, you'll internalize the patterns and start writing better prompts naturally.

## Contributing

Contributions welcome! See [CLAUDE.md](CLAUDE.md) for architecture details and development notes.

```bash
git clone https://github.com/yourname/claude-prompt-guide.git
cd claude-prompt-guide
pip install -e .
python -m prompt_guide "test prompt"
```

## License

MIT

