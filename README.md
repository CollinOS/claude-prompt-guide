
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