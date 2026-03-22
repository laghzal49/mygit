#!/usr/bin/env bash

set -euo pipefail

# --- Color Configuration ---
C_CYAN="\033[96m"
C_GREEN="\033[92m"
C_YELLOW="\033[93m"
C_RED="\033[91m"
C_RESET="\033[0m"

INSTALL_DIR="$HOME/.mygit_tool"
LAUNCHER_PATH="$HOME/.local/bin/mygit"
SERVICE_NAME="mygit-sync.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"

echo -e "${C_CYAN}🗑️  Uninstalling MyGit Automation Tool...${C_RESET}"

# 1. Stop and remove the systemd background daemon (if it exists)
if command -v systemctl >/dev/null 2>&1; then
    if systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
        echo -e "${C_YELLOW}⚙️ Stopping and removing background daemon (requires sudo)...${C_RESET}"
        sudo systemctl stop "$SERVICE_NAME" || true
        sudo systemctl disable "$SERVICE_NAME" || true
        sudo rm -f "$SERVICE_PATH"
        sudo systemctl daemon-reload
        echo -e "${C_GREEN}✅ Daemon removed.${C_RESET}"
    else
        echo -e "ℹ️  Daemon not found, skipping systemd cleanup."
    fi
fi

# 2. Remove the installation directory
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${C_YELLOW}📁 Removing installation directory ($INSTALL_DIR)...${C_RESET}"
    rm -rf "$INSTALL_DIR"
    echo -e "${C_GREEN}✅ Files removed.${C_RESET}"
fi

# 3. Remove the command-line launcher
if [ -f "$LAUNCHER_PATH" ]; then
    echo -e "${C_YELLOW}🗑️ Removing launcher executable ($LAUNCHER_PATH)...${C_RESET}"
    rm -f "$LAUNCHER_PATH"
    echo -e "${C_GREEN}✅ Launcher removed.${C_RESET}"
fi

# 4. Remove aliases from .bashrc and .zshrc
remove_alias() {
    rc_file="$1"
    if [ -f "$rc_file" ]; then
        if grep -q "alias mygit=" "$rc_file"; then
            echo -e "${C_YELLOW}📝 Removing alias from $rc_file...${C_RESET}"
            # Safely remove the line containing the alias
            grep -v "alias mygit=" "$rc_file" > "${rc_file}.tmp" && mv "${rc_file}.tmp" "$rc_file"
            echo -e "${C_GREEN}✅ Alias removed from $rc_file.${C_RESET}"
        fi
    fi
}

remove_alias "$HOME/.zshrc"
remove_alias "$HOME/.bashrc"

echo ""
echo -e "${C_GREEN}🎉 Uninstallation complete! Everything has been cleaned up.${C_RESET}"
echo -e "Run: ${C_CYAN}source ~/.zshrc${C_RESET} (or bashrc) to refresh your current terminal."
