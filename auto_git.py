import os
import time
import re
import sys

try:
    import github
    from git import Repo
    from dotenv import load_dotenv
except ImportError:
    print("Error: Missing dependencies. Run poetry install.")
    sys.exit(1)

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DESKTOP_PATH = os.path.expanduser("~/Desktop")
ENV_PATH = os.path.expanduser("~/.mygit_tool/.env")

C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_RESET = "\033[0m"


def get_clean_name(name):
    """Removes 'git' from the name and cleans up symbols."""
    clean = re.sub(r'git', '', name, flags=re.IGNORECASE)
    return clean.strip(' -_')


def get_syncable_folders():
    """Scans the Desktop and returns a list of folders ready to be synced."""
    valid_folders = []
    for folder in os.listdir(DESKTOP_PATH):
        path = os.path.join(DESKTOP_PATH, folder)
        if (
            "git" not in folder.lower()
            or not os.path.isdir(path)
            or folder.startswith('.')
        ):
            continue
        if os.path.exists(os.path.join(path, ".git")):
            continue
        valid_folders.append((folder, path))
    return valid_folders


def check_status():
    """Dry run feature to see what would be synced."""
    print(f"\n{C_CYAN}--- Status Check ---{C_RESET}")
    folders = get_syncable_folders()
    if not folders:
        print(
            f"{C_GREEN}Everything is up to date! "
            f"No pending folders.{C_RESET}"
        )
        return

    print(
        f"{C_YELLOW}Found {len(folders)} folder(s) "
        f"ready for GitHub:{C_RESET}"
    )
    for folder, _ in folders:
        clean_name = get_clean_name(folder)
        print(f"  📁 {folder}  =>  🌐 {clean_name}")


def update_token():
    """Allows the user to update their GitHub Token from the CLI."""
    global GITHUB_TOKEN
    print(f"\n{C_CYAN}--- Update GitHub Token ---{C_RESET}")
    print(
        f"{C_YELLOW}Tokens expire periodically. "
        f"Paste your new token here.{C_RESET}"
    )
    new_token = input("New Token: ").strip()

    if new_token:
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.write(f"GITHUB_TOKEN={new_token}\n")

        GITHUB_TOKEN = new_token
        print(f"{C_GREEN}✅ Token successfully updated!{C_RESET}")
    else:
        print(f"{C_RED}Update cancelled. Token cannot be empty.{C_RESET}")


def run_sync(commit_msg="Auto-sync"):
    """Core logic to initialize, create remote repo, and push."""
    if not GITHUB_TOKEN:
        print(
            f"{C_RED}Error: GITHUB_TOKEN not found! "
            f"Please use option 5 to set it.{C_RESET}"
        )
        return

    try:
        g = github.Github(GITHUB_TOKEN)
        user = g.get_user()
    except Exception as e:
        print(f"{C_RED}GitHub Auth Error: {e}{C_RESET}")
        print(
            f"{C_YELLOW}Your token may be invalid or expired. "
            f"Use option 5 to update it.{C_RESET}"
        )
        return

    folders = get_syncable_folders()
    if not folders:
        print(f"{C_GREEN}No new folders to sync.{C_RESET}")
        return

    for folder, path in folders:
        try:
            clean_name = get_clean_name(folder)
            print(f"{C_CYAN}Processing:{C_RESET} {folder} -> {clean_name}")

            repo = Repo.init(path)
            gh_repo = user.create_repo(clean_name, private=True)
            origin = repo.create_remote(
                "origin", gh_repo.clone_url
            )

            gitignore_path = os.path.join(path, ".gitignore")
            if not os.path.exists(gitignore_path):
                with open(gitignore_path, "w", encoding="utf-8") as f:
                    f.write(
                        "__pycache__/\nnode_modules/\n"
                        ".DS_Store\n.env\nvenv/\n"
                    )

            repo.index.add("*")
            repo.index.commit(commit_msg)
            origin.push(refspec='master:main')
            print(f"{C_GREEN}Successfully pushed: {clean_name}{C_RESET}")

        except Exception as e:
            print(f"{C_RED}Error processing {folder}: {e}{C_RESET}")


def menu():
    """Interactive CLI Menu for the user."""
    while True:
        print(f"\n{C_CYAN}╔════════════════════════════════════╗{C_RESET}")
        print(
            f"{C_CYAN}║{C_RESET}       {C_GREEN}🚀 MYGIT AUTOMATION 🚀"
            f"{C_RESET}       {C_CYAN}║{C_RESET}"
        )
        print(f"{C_CYAN}╠════════════════════════════════════╣{C_RESET}")
        print(
            f"{C_CYAN}║{C_RESET} 1. 📊 Check Status (Dry Run)"
            f"       {C_CYAN}║{C_RESET}"
        )
        print(
            f"{C_CYAN}║{C_RESET} 2. ⚡ Run Auto-Sync Now"
            f"            {C_CYAN}║{C_RESET}"
        )
        print(
            f"{C_CYAN}║{C_RESET} 3. 📝 Run Sync with Custom Commit"
            f"  {C_CYAN}║{C_RESET}"
        )
        print(
            f"{C_CYAN}║{C_RESET} 4. 🔄 Start Background Loop (1hr)"
            f"  {C_CYAN}║{C_RESET}"
        )
        print(
            f"{C_CYAN}║{C_RESET} 5. 🔑 Update GitHub Token"
            f"          {C_CYAN}║{C_RESET}"
        )
        print(
            f"{C_CYAN}║{C_RESET} 6. ❌ Exit"
            f"                         {C_CYAN}║{C_RESET}"
        )
        print(f"{C_CYAN}╚════════════════════════════════════╝{C_RESET}")

        choice = input(f"{C_YELLOW}Select an option (1-6): {C_RESET}").strip()

        if choice == '1':
            check_status()
        elif choice == '2':
            run_sync()
        elif choice == '3':
            msg = input(f"{C_YELLOW}Enter commit message: {C_RESET}").strip()
            run_sync(msg if msg else "Auto-sync")
        elif choice == '4':
            print(
                f"{C_GREEN}Running in background... "
                f"Press Ctrl+C to stop.{C_RESET}"
            )
            try:
                while True:
                    run_sync()
                    time.sleep(3600)
            except KeyboardInterrupt:
                print(f"\n{C_YELLOW}Background loop stopped.{C_RESET}")
        elif choice == '5':
            update_token()
        elif choice == '6':
            print(f"{C_CYAN}Goodbye!{C_RESET}")
            sys.exit()
        else:
            print(f"{C_RED}Invalid choice. Please select 1-6.{C_RESET}")


if __name__ == "__main__":
    menu()
