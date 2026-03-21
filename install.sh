#!/bin/bash

INSTALL_DIR="$HOME/.mygit_tool"

echo "🚀 Installing MyGit Automation Tool..."
mkdir -p "$INSTALL_DIR"

cp auto_git.py "$INSTALL_DIR/auto_git.py"
cd "$INSTALL_DIR"

if [ ! -f "pyproject.toml" ]; then
    poetry init --name mygit-tool \
                --dependency "PyGithub" \
                --dependency "GitPython" \
                --dependency "python-dotenv" \
                --dev-dependency "flake8" -n
    poetry install
fi

if ! grep -q "alias mygit=" ~/.zshrc; then
    echo "alias mygit='(cd $INSTALL_DIR && poetry run python3 auto_git.py)'" >> ~/.zshrc
    echo "✅ Alias 'mygit' added to .zshrc"
fi

if [ ! -f ".env" ]; then
    touch .env
    echo "✅ Created .env file in $INSTALL_DIR."
    echo "⚠️  IMPORTANT: Please open ~/.mygit_tool/.env and add: GITHUB_TOKEN=your_token_here"
fi

echo "🎉 Installation complete! Restart your terminal or run 'source ~/.zshrc'"