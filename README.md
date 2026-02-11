# Claude Prompt Guide

An interactive CLI tool that coaches you into writing better prompts for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Instead of rewriting your prompt for you, it asks the right follow-up questions so Claude Code gets the context it needs on the first try.

**No extra API key needed** — it uses your existing Claude Code authentication.

## Demo

```
$ claude
> /guide fix the auth bug

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

## How It Works

1. You type `/guide` followed by a casual prompt inside Claude Code
2. The tool asks you 2-4 targeted follow-up questions specific to your task
3. You answer in a few words each (or press enter to skip any)
4. It assembles everything into a clean, context-rich prompt
5. You review and choose to send, edit, or cancel

The questions are generated dynamically by Claude — not from a static template — so they're always relevant to what you're actually asking.

**Important:** `/guide` is a command you use per-prompt, not a toggle. When you want the guided experience, use `/guide your prompt`. When you don't, just type your prompt normally.

## Prerequisites

- Python 3.9+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated

## Install

### Step 1: Clone the repo

```bash
git clone https://github.com/yourname/claude-prompt-guide.git
```

### Step 2: Set up the slash command

Copy the standalone script into your Claude Code hooks directory:

```bash
mkdir -p ~/.claude/hooks
cp claude-prompt-guide/standalone/prompt-guide.py ~/.claude/hooks/prompt-guide.py
chmod +x ~/.claude/hooks/prompt-guide.py
```

Then create (or edit) `~/.claude/commands/guide.md`:

```bash
mkdir -p ~/.claude/commands
cat > ~/.claude/commands/guide.md << 'EOF'
Run the prompt guide script to help the user write a better prompt.
Execute: python3 ~/.claude/hooks/prompt-guide.py "$ARGUMENTS"
Use the output as your task instructions and proceed with the task.
EOF
```

### Step 3: Use it

Open Claude Code and type:

```
/guide fix the auth bug
```

### Optional: Install rich for a nicer UI

```bash
pip install rich
```

The tool works fine without it — just falls back to plain text prompts.

## Alternative Usage

If you prefer not to use the slash command, there are other ways to run it.

### Standalone (outside Claude Code)

```bash
# With a prompt
python3 ~/.claude/hooks/prompt-guide.py "add pagination to the users API"

# Interactive — it will ask you what you want to do
python3 ~/.claude/hooks/prompt-guide.py

# Quiet mode — outputs only the final prompt, no UI
python3 ~/.claude/hooks/prompt-guide.py -q "fix the login bug"
```

### Shell alias

Add to `~/.bashrc` or `~/.zshrc`:

```bash
cg() {
    local enriched
    enriched=$(python3 ~/.claude/hooks/prompt-guide.py -q "$1")
    if [ $? -eq 0 ] && [ -n "$enriched" ]; then
        claude "$enriched"
    fi
}
```

Reload your shell, then:

```bash
cg "add dark mode"
```

### Piped directly into Claude Code

```bash
claude "$(python3 ~/.claude/hooks/prompt-guide.py -q 'fix the login bug')"
```

## Why This Instead of a Prompt Rewriter?

Prompt rewriters change your words behind the scenes. This tool **asks you questions** instead. The difference:

- **You stay in control** of what gets sent
- **You learn** what context matters over time
- **Your intent** is never misinterpreted by a rewriter
- **The context** comes from you — the person who actually knows the codebase

After using this for a while, you'll start writing better prompts naturally and won't need the tool as much. That's the point.

## Uninstall

```bash
rm ~/.claude/hooks/prompt-guide.py
rm ~/.claude/commands/guide.md
rm -rf /path/to/claude-prompt-guide  # the cloned repo
```

## Contributing

Contributions welcome! See [CLAUDE.md](CLAUDE.md) for architecture details and development notes.

```bash
git clone https://github.com/CollinOS/claude-prompt-guide.git
cd claude-prompt-guide
python3 standalone/prompt-guide.py "test prompt"
```

## License

MIT