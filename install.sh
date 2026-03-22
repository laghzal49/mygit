#!/usr/bin/env bash

set -euo pipefail

# --- Color Configuration ---
C_CYAN="\033[96m"
C_GREEN="\033[92m"
C_YELLOW="\033[93m"
C_RED="\033[91m"
C_RESET="\033[0m"

INSTALL_DIR="$HOME/.mygit_tool"
SCRIPT_PATH="$INSTALL_DIR/auto_git.py"
ENV_PATH="$INSTALL_DIR/.env"
BIN_DIR="$HOME/.local/bin"
LAUNCHER_PATH="$BIN_DIR/mygit"
ALIAS_LINE="alias mygit='(cd $INSTALL_DIR && poetry run python3 auto_git.py)'"

echo -e "${C_CYAN}🚀 Installing MyGit Automation Tool...${C_RESET}"

if ! command -v poetry >/dev/null 2>&1; then
    echo -e "${C_RED}❌ Poetry is required but not installed.${C_RESET}"
    echo "Install Poetry first, then re-run: ./install.sh"
    exit 1
fi

if [ ! -f "auto_git.py" ]; then
    echo -e "${C_RED}❌ Error: auto_git.py not found in the current directory.${C_RESET}"
    exit 1
fi

mkdir -p "$INSTALL_DIR"
cp auto_git.py "$SCRIPT_PATH"
cd "$INSTALL_DIR"

if [ ! -f "pyproject.toml" ]; then
    echo -e "${C_YELLOW}📦 Initializing Poetry project...${C_RESET}"
    poetry init --name mygit-tool \
                --dependency "PyGithub" \
                --dependency "GitPython" \
                --dependency "python-dotenv" \
                --dev-dependency "flake8" \
                -n
fi

echo -e "${C_YELLOW}📥 Installing dependencies...${C_RESET}"
poetry install --no-interaction --no-root

touch "$ENV_PATH"

# Setup default .env values
if ! grep -q '^GITHUB_TOKEN=' "$ENV_PATH"; then echo "GITHUB_TOKEN=" >> "$ENV_PATH"; fi
if ! grep -q '^PUSH_METHOD=' "$ENV_PATH"; then echo "PUSH_METHOD=https" >> "$ENV_PATH"; fi
if ! grep -q '^SCAN_PATH=' "$ENV_PATH"; then echo "SCAN_PATH=$HOME/Desktop" >> "$ENV_PATH"; fi

add_alias_if_missing() {
    rc_file="$1"
    if [ ! -f "$rc_file" ]; then touch "$rc_file"; fi
    if ! grep -Fq "alias mygit=" "$rc_file"; then
        echo "$ALIAS_LINE" >> "$rc_file"
        echo -e "${C_GREEN}✅ Alias 'mygit' added to $rc_file${C_RESET}"
    fi
}

add_alias_if_missing "$HOME/.zshrc"
add_alias_if_missing "$HOME/.bashrc"

mkdir -p "$BIN_DIR"
cat > "$LAUNCHER_PATH" <<EOF
#!/usr/bin/env bash
cd "$INSTALL_DIR" || exit 1
exec poetry run python3 auto_git.py "\$@"
EOF
chmod +x "$LAUNCHER_PATH"

if ! grep -Fq 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.bashrc"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi
if ! grep -Fq 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.zshrc"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
fi

echo -e "${C_GREEN}✅ Installed script at: $SCRIPT_PATH${C_RESET}"
echo -e "${C_GREEN}✅ Launcher created at: $LAUNCHER_PATH${C_RESET}"
echo -e "${C_GREEN}✅ Environment file ready at: $ENV_PATH${C_RESET}"

# --- DAEMON INSTALLATION PROMPT ---
echo ""
echo -e "${C_CYAN}--- Background Daemon Setup ---${C_RESET}"
if command -v systemctl >/dev/null 2>&1; then
    read -p "$(echo -e ${C_YELLOW}Do you want to install the background auto-sync daemon? [y/N] ${C_RESET})" install_daemon
    if [[ "$install_daemon" =~ ^[Yy]$ ]]; then
        echo -e "${C_CYAN}⚙️ Setting up systemd daemon (requires sudo)...${C_RESET}"
        
        SERVICE_PATH="/etc/systemd/system/mygit-sync.service"
        USER_NAME=$(whoami)
        POETRY_PATH=$(command -v poetry)
        
        sudo bash -c "cat > $SERVICE_PATH" <<EOL
[Unit]
Description=MyGit Auto Sync Daemon
After=network.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$INSTALL_DIR
ExecStart=$POETRY_PATH run python3 $SCRIPT_PATH --daemon
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
EOL

        sudo systemctl daemon-reload
        sudo systemctl enable mygit-sync
        sudo systemctl start mygit-sync
        echo -e "${C_GREEN}✅ Daemon installed and running in the background!${C_RESET}"
        echo -e "   Check status with: ${C_CYAN}sudo systemctl status mygit-sync${C_RESET}"
    else
        echo -e "${C_YELLOW}Skipping daemon installation. You can still run 'mygit' manually.${C_RESET}"
    fi
else
    echo -e "${C_YELLOW}systemctl not found. Skipping systemd daemon setup (likely on macOS or non-systemd Linux).${C_RESET}"
fi

echo ""
echo -e "${C_GREEN}🎉 Installation complete!${C_RESET}"
echo -e "⚠️  ${C_RED}Action Required:${C_RESET} Set your token in $ENV_PATH (GITHUB_TOKEN=your_token_here)"
echo -e "Run: ${C_CYAN}source ~/.zshrc${C_RESET} (or bashrc) to use the 'mygit' command immediately."