import os
import time
import re
import sys

try:
    import github
    from github.GithubException import GithubException
    from git import Repo
    from dotenv import load_dotenv
except ImportError:
    print("Error: Missing dependencies. Run poetry install.")
    sys.exit(1)

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DESKTOP_PATH = os.path.expanduser("~/Desktop")

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


def run_sync(commit_msg="Auto-sync"):
    """Core logic to initialize, create remote repo, and push."""
    if not GITHUB_TOKEN:
        print(f"{C_RED}Error: GITHUB_TOKEN not found in .env{C_RESET}")
        return

    try:
        g = github.Github(auth=github.Auth.Token(GITHUB_TOKEN))
        user = g.get_user()
    except Exception as e:
        print(f"{C_RED}GitHub Auth Error: {e}{C_RESET}")
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

        except GithubException as e:
            error_data = getattr(e, "data", {})
            if isinstance(error_data, dict):
                error_message = error_data.get("message", "")
            else:
                error_message = str(e)

            if (
                e.status == 403
                and "Resource not accessible by personal access token"
                in error_message
            ):
                print(
                    f"{C_RED}GitHub token lacks permission to create "
                    f"repositories.{C_RESET}"
                )
                print(
                    f"{C_YELLOW}Use a token that can create repos "
                    f"(classic PAT with 'repo' scope, or a fine-grained token "
                    f"with repository administration write access).{C_RESET}"
                )
                return

            print(f"{C_RED}GitHub API error for {folder}: {e}{C_RESET}")

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
            f"{C_CYAN}║{C_RESET} 5. ❌ Exit"
            f"                         {C_CYAN}║{C_RESET}"
        )
        print(f"{C_CYAN}╚════════════════════════════════════╝{C_RESET}")

        choice = input(f"{C_YELLOW}Select an option (1-5): {C_RESET}").strip()

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
            print(f"{C_CYAN}Goodbye!{C_RESET}")
            sys.exit()
        else:
            print(f"{C_RED}Invalid choice. Please select 1-5.{C_RESET}")


if __name__ == "__main__":
    menu()
