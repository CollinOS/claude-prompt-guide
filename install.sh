#!/bin/bash
set -e

echo "Claude Prompt Guide — Installer"
echo "================================"
echo ""

# Check for python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found."
    exit 1
fi

# Check for claude CLI
if ! command -v claude &> /dev/null; then
    echo "Warning: Claude Code CLI not found."
    echo "Install it first: https://docs.anthropic.com/en/docs/claude-code"
    echo ""
fi

echo "Choose install method:"
echo "  1) pip install (package mode)"
echo "  2) pipx install (isolated, recommended)"
echo "  3) Single file (no dependencies, drop into ~/.claude/hooks/)"
echo ""
read -p "Choice [1/2/3]: " choice

case $choice in
    1)
        echo "Installing via pip..."
        pip install claude-prompt-guide
        echo ""
        echo "Done! Run: prompt-guide \"your prompt here\""
        echo "Optional: pip install rich  (for nicer UI)"
        ;;
    2)
        if ! command -v pipx &> /dev/null; then
            echo "pipx not found. Installing pipx first..."
            pip install pipx
            pipx ensurepath
        fi
        echo "Installing via pipx..."
        pipx install claude-prompt-guide
        echo ""
        echo "Done! Run: prompt-guide \"your prompt here\""
        echo "Optional: pipx inject claude-prompt-guide rich  (for nicer UI)"
        ;;
    3)
        echo "Installing standalone version..."
        mkdir -p ~/.claude/hooks
        curl -o ~/.claude/hooks/prompt-guide.py \
            https://raw.githubusercontent.com/yourname/claude-prompt-guide/main/standalone/prompt-guide.py
        chmod +x ~/.claude/hooks/prompt-guide.py
        echo ""
        echo "Done! Run: python3 ~/.claude/hooks/prompt-guide.py \"your prompt here\""
        ;;
    *)
        echo "Invalid choice."
        exit 1
        ;;
esac

echo ""
echo "Recommended: add a shell alias for convenience."
echo "Add this to your ~/.bashrc or ~/.zshrc:"
echo ""
echo '  cg() {'
echo '      local enriched'
echo '      enriched=$(prompt-guide -q "$1")'
echo '      if [ $? -eq 0 ] && [ -n "$enriched" ]; then'
echo '          claude "$enriched"'
echo '      fi'
echo '  }'
echo ""
