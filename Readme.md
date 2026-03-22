# 🚀 MyGit Automation Tool

MyGit is a lightweight CLI that scans your target directory for folders containing `git` in the name, initializes local Git repositories, creates private GitHub repositories, and pushes them automatically.

**Author:** [@laghzal49](https://github.com/laghzal49)

---

## 🤔 Why this tool?

Manual flow (`git init` → create repo on GitHub → add remote → first push) gets repetitive when building many small projects.

MyGit automates this by:
- Detecting eligible folders in your configured scan path (default: `~/Desktop`)
- Sanitizing repository names before creating remote repos
- Creating private repos via GitHub API
- Generating a starter `.gitignore`
- Committing and pushing automatically

It also supports background syncing via a systemd service on Linux.

---

## ✨ Features

- Smart folder detection (`git` in name, case-insensitive)
- Safe repo-name cleanup (removes standalone `git` tokens)
- Auto `.gitignore` generation
- Cursus-style interactive TUI menu
- Curses folder sub-menu with multi-select (`Space` to toggle)
- Push method toggle (`HTTPS` / `SSH`)
- Configurable scan path
- Optional systemd daemon mode (`--daemon`)

---

## 🔑 GitHub Token Setup

Use a Personal Access Token (PAT), not your account password.

### Fine-grained token (recommended)

Set at least:
- **Repository access:** All repositories (or required selected repos)
- **Administration:** Read and write
- **Contents:** Read and write
- **Metadata:** Read-only

Save it in:

```env
~/.mygit_tool/.env
GITHUB_TOKEN=your_token_here
```

---

## ⚙️ Installation

### Prerequisites

- Python 3
- Poetry

### Install

```bash
./install.sh
```

The installer will:
- Copy `auto_git.py` to `~/.mygit_tool/`
- Install dependencies with Poetry
- Create `~/.local/bin/mygit` launcher
- Configure shell integration (`.bashrc` and `.zshrc`)
- Create/update `~/.mygit_tool/.env` defaults
- Optionally install the systemd daemon

After install:

```bash
source ~/.bashrc
# or
source ~/.zshrc
```

---

## 💻 Usage

Start the tool:

```bash
mygit
```

The menu uses a Cursus-style terminal UI (`curses`):
- Use `↑` / `↓` to navigate
- Press `Enter` to execute an option
- In folder selection, use `Space` to select/unselect multiple folders

### Folder rules

A folder is syncable if:
- It is under `SCAN_PATH` (default: `~/Desktop`)
- Its name contains `git`
- It is not already a git repo (`.git` missing)

Examples:
- `maze-project-git` → `maze-project`
- `Git_PushSwap` → `PushSwap`
- `python_scripts` → ignored

### CLI menu

1. Check Status (Dry Run)
2. Run Auto-Sync Now
3. Run Sync with Custom Commit
4. Start Background Loop (1hr)
5. Switch Folders (Multi-Select)
6. Switch Push Method (SSH/HTTPS)
7. Change Scan Directory
8. Exit

Note: option `7` uses standard typed path input for easier directory entry.

---

## 🤖 Background Daemon (Linux)

If installed via `install.sh`, manage it with:

```bash
sudo systemctl status mygit-sync
sudo systemctl stop mygit-sync
sudo systemctl start mygit-sync
journalctl -u mygit-sync -f
```

---

## 🗑️ Uninstallation

```bash
./uninstall.sh
```

This script removes:
- `~/.mygit_tool`
- `~/.local/bin/mygit`
- `mygit` alias entries in shell rc files
- systemd daemon (`mygit-sync`) if installed

---

## 🛠 Troubleshooting

### 403: Resource not accessible by personal access token

Your token lacks required repository permissions.

Fix:
1. Create a new PAT with required permissions
2. Update `GITHUB_TOKEN` in `~/.mygit_tool/.env`
3. Retry sync

### `mygit: command not found`

Run:

```bash
source ~/.bashrc
# or
source ~/.zshrc
```

Also ensure `~/.local/bin` is in your `PATH`.

### SSH push issues

If using SSH mode, make sure your SSH key is added to GitHub and your agent is running.

---

## 📝 License

Created by [@laghzal49](https://github.com/laghzal49). Feel free to fork and adapt.