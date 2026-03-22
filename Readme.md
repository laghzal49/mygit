# 🚀 MyGit Automation Tool

MyGit is a lightweight CLI that scans your Desktop for folders containing `git` in the name, initializes local Git repos, creates private GitHub repositories, and pushes automatically.

**Author:** [@laghzal49](https://github.com/laghzal49)

---

## 🤔 Why this tool?

Manual workflow (`git init` → create repo on GitHub → add remote → first push) gets repetitive when you create many small projects.

MyGit automates that flow by:
1. Detecting eligible folders on `~/Desktop`.
2. Sanitizing the remote repository name (removes standalone `git` tags).
3. Creating a private GitHub repository.
4. Generating a starter `.gitignore`.
5. Committing and pushing your code.

---

## ✨ Features

- Smart folder detection (`git` in folder name, case-insensitive).
- Safe repo-name cleanup before creating GitHub repositories.
- Auto-generated `.gitignore` for common junk files.
- Interactive CLI menu with status check and loop mode.
- Simple token-based authentication with `.env`.

### 🆕 New Feature

- Updated GitHub authentication to modern PyGithub token auth (`github.Auth.Token`) to avoid deprecation warnings.
- Added clearer 403 permission guidance when a token cannot create repositories.
- Added folder targeting with option `5` to sync one selected folder.
- Added push-method toggle with option `6` to switch between HTTPS and SSH.

---

## 🔑 GitHub token setup

Use a Personal Access Token (PAT), not your password.

### Fine-grained token (recommended)

When creating the token in GitHub settings:
- Repository access: **All repositories** (or include the repos you need).
- Repository permissions:
  - **Administration:** Read and write
  - **Contents:** Read and write
  - **Metadata:** Read-only

Then save your token in `~/.mygit_tool/.env`:

```env
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

After install:
1. Run `mygit`
2. Add your PAT to `~/.mygit_tool/.env` (`GITHUB_TOKEN=...`)
3. Run option `2` to sync

Installer defaults in `~/.mygit_tool/.env`:

```env
GITHUB_TOKEN=
PUSH_METHOD=https
SCAN_PATH=~/Desktop
```

---

## 💻 Usage

### Folder rule

A folder is eligible only if:
- It is under your configured `SCAN_PATH` (default: `~/Desktop`)
- Its name contains `git`

Examples:
- `maze-project-git` → creates repo `maze-project`
- `Git_PushSwap` → creates repo `PushSwap`
- `python_scripts` → ignored

### Menu options

1. Check Status (Dry Run)
2. Run Auto-Sync Now
3. Run Sync with Custom Commit
4. Start Background Loop (1hr)
5. Switch Folder (sync one selected folder)
6. Switch Push Method (SSH/HTTPS)
7. Change Scan Directory
8. Exit

---

## 🛠 Troubleshooting

### 403: Resource not accessible by personal access token

This means your token does not have enough permission to create repositories.

Fix:
1. Create a new PAT with the permissions listed above.
2. Update `GITHUB_TOKEN` in `~/.mygit_tool/.env`.
3. Run option `2` again.

### Auth/Push issues

- Confirm token is saved in `~/.mygit_tool/.env` as `GITHUB_TOKEN=...`.
- If using SSH mode, make sure your SSH key is configured in GitHub.
- Re-run `bash install.sh` after pulling latest changes.

---

## 📝 License

Created by tlaghzal. Fork and adapt for your workflow.