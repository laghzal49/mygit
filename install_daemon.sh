#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

C_CYAN="\033[96m"
C_GREEN="\033[92m"
C_YELLOW="\033[93m"
C_RED="\033[91m"
C_RESET="\033[0m"

echo -e "${C_CYAN}--- MyGit Sync Daemon Installer ---${C_RESET}"

# Get the current user and directory automatically
USER_NAME=$(whoami)
CURRENT_DIR=$(pwd)
PYTHON_PATH=$(which python3)

# Ask for the exact name of your python file
echo -e "${C_YELLOW}"
read -p "Enter the name of your Python script (e.g., mygit.py): " SCRIPT_NAME
echo -e "${C_RESET}"

# Verify the file actually exists
if [ ! -f "$CURRENT_DIR/$SCRIPT_NAME" ]; then
    echo -e "${C_RED}Error: '$SCRIPT_NAME' not found in $CURRENT_DIR${C_RESET}"
    exit 1
fi

SERVICE_PATH="/etc/systemd/system/mygit-sync.service"

echo -e "Creating service file at ${SERVICE_PATH}..."

# Generate the systemd service file
sudo bash -c "cat > $SERVICE_PATH" <<EOL
[Unit]
Description=MyGit Auto Sync Daemon
After=network.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$CURRENT_DIR
ExecStart=$PYTHON_PATH $CURRENT_DIR/$SCRIPT_NAME --daemon
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
EOL

echo -e "Reloading systemd, enabling, and starting the service..."

# Reload and start the daemon
sudo systemctl daemon-reload
sudo systemctl enable mygit-sync
sudo systemctl start mygit-sync

echo -e "${C_GREEN}Installation complete! The daemon is now running in the background.${C_RESET}"
echo -e "You can check its status anytime with: ${C_CYAN}sudo systemctl status mygit-sync${C_RESET}"