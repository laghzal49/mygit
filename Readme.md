# 🚀 MyGit Automation Tool

A lightweight, interactive CLI tool that automatically detects specific folders on your Desktop, initializes them as Git repositories, creates private repositories on GitHub, and pushes your code seamlessly. 

Built to keep your workflow fast, your Desktop organized, and your GitHub profile green.

**Authored by:** [@laghzal49](https://github.com/laghzal49) (Tarik)

---

## 🤔 Why use this tool?

If you create a lot of mini-projects, scripts, or daily exercises (like the projects at 1337), manually running `git init`, going to GitHub, clicking "New Repository", copying the remote URL, and pushing can get incredibly tedious. 

**MyGit** automates this entirely. Just name your folder with the word `git` in it (e.g., `maze-project-git`), and this tool will:
1. Strip the "git" tag (renaming the repo to `maze-project`).
2. Auto-generate a safe `.gitignore` so you don't upload junk files.
3. Create a private repository on your GitHub account.
4. Push your initial code.

All of this happens in the background, or with a single terminal command.

---

## ✨ Key Features
* **Smart Detection:** Only targets folders on your Desktop containing the word `git` (case-insensitive).
* **Auto-Sanitization:** Cleans up folder names. `My_App-git` becomes `My_App` on GitHub.
* **Auto `.gitignore`:** Automatically skips compiling binaries, `node_modules`, `.DS_Store`, and `.env` files.
* **Empty Folder Protection:** The script won't crash or create empty repos; it waits until you actually put code in the folder.
* **Interactive Colored Menu:** Easy-to-use CLI interface.
* **Flake8 Compliant:** Strict adherence to PEP 8 Python standards.

---

## 🔑 The GitHub Token: What, Why, and How?

### Why do you need a token?
To create repositories on your behalf, this script needs to authenticate with GitHub. Instead of using your actual account password (which is insecure and blocked by GitHub for API use), we use a **Personal Access Token (PAT)**. Think of it as a temporary, restricted key that only has permission to manage repositories.

### How to get your Token (Step-by-Step)
1. Log in to your GitHub account on your browser.
2. Click your profile picture in the top right corner and select **Settings**.
3. Scroll all the way down the left sidebar and click **<> Developer settings**.
4. Click **Personal access tokens**, then select **Fine-grained tokens**.
5. Click the **Generate new token** button.
6. Fill out the details:
   * **Token name:** `MyGit Automation CLI` (or whatever you prefer).
   * **Expiration:** Set it to 90 days or custom (you can regenerate it later).
   * **Repository access:** Select **All repositories**.
7. Under **Permissions**, click **Repository permissions** and change:
   * **Administration:** Read and write
   * **Contents:** Read and write
   * **Metadata:** Read-only (usually set by default)
8. Click **Generate token** at the bottom.
9. ⚠️ **COPY YOUR TOKEN NOW!** GitHub will only show it to you this one time.

### How to use the Token securely
Never paste your token directly into a Python script! If you accidentally upload that script, anyone can access your GitHub. Instead, we use a hidden `.env` file. Our installer sets this up for you automatically.

---

## ⚙️ Installation

### Prerequisites
Make sure you have **Python 3** and **Poetry** installed on your system.

### Quick Install
1. Clone or download this repository.
2. Open your terminal in the downloaded folder.
3. Run the installer script:
   ```bash
   bash install.sh