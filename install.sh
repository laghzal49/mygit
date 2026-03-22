#!/usr/bin/env bash

set -euo pipefail

INSTALL_DIR="$HOME/.mygit_tool"
SCRIPT_PATH="$INSTALL_DIR/auto_git.py"
ENV_PATH="$INSTALL_DIR/.env"
ALIAS_LINE="alias mygit='(cd $INSTALL_DIR && poetry run python3 auto_git.py)'"

echo "🚀 Installing MyGit Automation Tool..."

if ! command -v poetry >/dev/null 2>&1; then
    echo "❌ Poetry is required but not installed."
    echo "Install Poetry first, then re-run: ./install.sh"
    exit 1
fi

mkdir -p "$INSTALL_DIR"
cp auto_git.py "$SCRIPT_PATH"
cd "$INSTALL_DIR"

if [ ! -f "pyproject.toml" ]; then
    poetry init --name mygit-tool \
                --dependency "PyGithub" \
                --dependency "GitPython" \
                --dependency "python-dotenv" \
                --dev-dependency "flake8" \
                -n
fi

poetry install --no-interaction

touch "$ENV_PATH"

if ! grep -q '^GITHUB_TOKEN=' "$ENV_PATH"; then
    echo "GITHUB_TOKEN=" >> "$ENV_PATH"
fi

if ! grep -q '^PUSH_METHOD=' "$ENV_PATH"; then
    echo "PUSH_METHOD=https" >> "$ENV_PATH"
fi

if ! grep -q '^SCAN_PATH=' "$ENV_PATH"; then
    echo "SCAN_PATH=$HOME/Desktop" >> "$ENV_PATH"
fi

add_alias_if_missing() {
    rc_file="$1"
    if [ ! -f "$rc_file" ]; then
        touch "$rc_file"
    fi

    if ! grep -Fq "alias mygit=" "$rc_file"; then
        echo "$ALIAS_LINE" >> "$rc_file"
        echo "✅ Alias 'mygit' added to $rc_file"
    fi
}

add_alias_if_missing "$HOME/.zshrc"
add_alias_if_missing "$HOME/.bashrc"

echo "✅ Installed script at: $SCRIPT_PATH"
echo "✅ Environment file ready at: $ENV_PATH"
echo "⚠️  Set your token in $ENV_PATH (GITHUB_TOKEN=your_token_here)"
echo "🎉 Installation complete!"
echo "Run: source ~/.zshrc  (or source ~/.bashrc)"