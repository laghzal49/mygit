import os
import time
import re
import sys
import curses

try:
    import github
    from github.GithubException import GithubException
    from git import Repo
    from dotenv import load_dotenv
except ImportError:
    print("Error: Missing dependencies. Run poetry install.")
    sys.exit(1)

ENV_PATH = os.path.expanduser("~/.mygit_tool/.env")
load_dotenv(ENV_PATH)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DESKTOP_PATH = os.path.expanduser(
    os.getenv("SCAN_PATH", "~/Desktop")
)
PUSH_METHOD = os.getenv("PUSH_METHOD", "https").lower()
SELECTED_FOLDER = None

C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_RESET = "\033[0m"


def save_config():
    """Persist tool configuration values to ~/.mygit_tool/.env."""
    os.makedirs(os.path.dirname(ENV_PATH), exist_ok=True)
    with open(ENV_PATH, "w", encoding="utf-8") as env_file:
        if GITHUB_TOKEN:
            env_file.write(f"GITHUB_TOKEN={GITHUB_TOKEN}\n")
        env_file.write(f"SCAN_PATH={DESKTOP_PATH}\n")
        env_file.write(f"PUSH_METHOD={PUSH_METHOD}\n")


def get_clean_name(name):
    """Removes standalone 'git' tokens and cleans up symbols."""
    clean = re.sub(
        r"(?i)(^|[-_\s])git(?=$|[-_\s])",
        r"\1",
        name,
    )
    clean = re.sub(r"[-_\s]{2,}", "-", clean).strip(" -_")
    if not clean:
        return name.strip(" -_")
    return clean


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
    print(
        f"{C_YELLOW}Push method:{C_RESET} {PUSH_METHOD.upper()}"
    )

    if SELECTED_FOLDER:
        print(
            f"{C_YELLOW}Selected folder:{C_RESET} "
            f"{SELECTED_FOLDER[0]}"
        )

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


def switch_folder():
    """Allow the user to pick one target folder for sync."""
    global SELECTED_FOLDER

    folders = get_syncable_folders()
    if not folders:
        print(
            f"{C_YELLOW}No available folders to select right now.{C_RESET}"
        )
        SELECTED_FOLDER = None
        return

    print(f"\n{C_CYAN}--- Switch Folder ---{C_RESET}")
    print(f"{C_YELLOW}0. All folders (default){C_RESET}")
    for index, (folder, _) in enumerate(folders, start=1):
        print(f"{C_YELLOW}{index}. {folder}{C_RESET}")

    choice = input("Select folder number: ").strip()
    if choice == "0":
        SELECTED_FOLDER = None
        print(f"{C_GREEN}Selection cleared: syncing all folders.{C_RESET}")
        return

    if not choice.isdigit():
        print(f"{C_RED}Invalid selection.{C_RESET}")
        return

    selected_index = int(choice)
    if selected_index < 1 or selected_index > len(folders):
        print(f"{C_RED}Selection out of range.{C_RESET}")
        return

    SELECTED_FOLDER = folders[selected_index - 1]
    print(
        f"{C_GREEN}Selected folder: {SELECTED_FOLDER[0]}{C_RESET}"
    )


def switch_push_method():
    """Toggle push method between HTTPS and SSH."""
    global PUSH_METHOD

    if PUSH_METHOD == "https":
        PUSH_METHOD = "ssh"
    else:
        PUSH_METHOD = "https"

    save_config()
    print(
        f"{C_GREEN}Push method switched to "
        f"{PUSH_METHOD.upper()}.{C_RESET}"
    )


def change_directory():
    """Change the base directory for scanning folders."""
    global DESKTOP_PATH
    global SELECTED_FOLDER

    print(f"\n{C_CYAN}--- Change Directory ---{C_RESET}")
    new_path = input(
        f"{C_YELLOW}Enter new directory path: {C_RESET}"
    ).strip()

    if not new_path:
        print(f"{C_RED}Directory cannot be empty.{C_RESET}")
        return

    new_path = os.path.abspath(os.path.expanduser(new_path))

    if not os.path.isdir(new_path):
        print(f"{C_RED}Invalid directory.{C_RESET}")
        return

    DESKTOP_PATH = new_path
    SELECTED_FOLDER = None
    save_config()
    print(f"{C_GREEN}Directory changed to: {DESKTOP_PATH}{C_RESET}")


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

    if SELECTED_FOLDER:
        selected_name = SELECTED_FOLDER[0]
        folders = [
            folder_info
            for folder_info in folders
            if folder_info[0] == selected_name
        ]

        if not folders:
            print(
                f"{C_YELLOW}Selected folder is not available anymore. "
                f"Use option 5 to choose again.{C_RESET}"
            )
            return

    for folder, path in folders:
        try:
            clean_name = get_clean_name(folder)
            print(f"{C_CYAN}Processing:{C_RESET} {folder} -> {clean_name}")

            repo = Repo.init(path)
            gh_repo = user.create_repo(clean_name, private=True)
            if PUSH_METHOD == "ssh":
                remote_url = gh_repo.ssh_url
            else:
                remote_url = gh_repo.clone_url

            origin = repo.create_remote("origin", remote_url)

            gitignore_path = os.path.join(path, ".gitignore")
            if not os.path.exists(gitignore_path):
                with open(gitignore_path, "w", encoding="utf-8") as f:
                    f.write(
                        "__pycache__/\nnode_modules/\n"
                        ".DS_Store\n.env\nvenv/\n"
                    )

            repo.index.add("*")
            repo.index.commit(commit_msg)

            if repo.active_branch.name != "main":
                repo.git.branch("-M", "main")

            if PUSH_METHOD == "https":
                auth_url = gh_repo.clone_url.replace(
                    "https://", f"https://{GITHUB_TOKEN}@"
                )
                origin.set_url(auth_url)
                try:
                    origin.push(refspec="main:main")
                finally:
                    origin.set_url(gh_repo.clone_url)
            else:
                origin.push(refspec="main:main")

            print(
                f"{C_GREEN}Successfully pushed "
                f"({PUSH_METHOD.upper()}): {clean_name}{C_RESET}"
            )

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


def curses_menu(stdscr):
    """Draw the interactive curses menu and return selected option."""
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)

    menu_items = [
        "📊 Check Status (Dry Run)",
        "⚡ Run Auto-Sync Now",
        "📝 Run Sync with Custom Commit",
        "🔄 Start Background Loop (1hr)",
        "📁 Switch Folder",
        "🔀 Switch Push Method (SSH/HTTPS)",
        "📂 Change Scan Directory",
        "❌ Exit",
    ]

    current_row = 0

    while True:
        stdscr.clear()
        selected_name = (
            SELECTED_FOLDER[0] if SELECTED_FOLDER else "All folders"
        )

        stdscr.addstr(
            1,
            2,
            "╔════════════════════════════════════════════════════╗",
            curses.color_pair(1),
        )
        stdscr.addstr(
            2,
            2,
            "║ 🚀 MYGIT AUTOMATION · CURSUS TUI                  ║",
            curses.color_pair(1),
        )
        stdscr.addstr(
            3,
            2,
            "╠════════════════════════════════════════════════════╣",
            curses.color_pair(1),
        )
        stdscr.addstr(
            4,
            2,
            f"║ Scan path : {DESKTOP_PATH:<38} ║",
            curses.color_pair(1),
        )
        stdscr.addstr(
            5,
            2,
            f"║ Push mode : {PUSH_METHOD.upper():<38} ║",
            curses.color_pair(1),
        )
        stdscr.addstr(
            6,
            2,
            f"║ Selected  : {selected_name:<38} ║",
            curses.color_pair(1),
        )
        stdscr.addstr(
            7,
            2,
            "╠════════════════════════════════════════════════════╣",
            curses.color_pair(1),
        )

        for index, item in enumerate(menu_items):
            y_pos = 9 + index
            if index == current_row:
                stdscr.addstr(y_pos, 4, item.ljust(46), curses.color_pair(3))
            else:
                stdscr.addstr(y_pos, 4, item.ljust(46), curses.color_pair(1))

        stdscr.addstr(
            18,
            2,
            "╚════════════════════════════════════════════════════╝",
            curses.color_pair(1),
        )
        stdscr.addstr(
            20,
            2,
            "Use ↑/↓ arrows to navigate, ENTER to select.",
            curses.color_pair(2),
        )
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu_items) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            return current_row + 1


def interactive_loop():
    """Handle curses UI and execute selected actions in standard terminal."""
    while True:
        choice = curses.wrapper(curses_menu)
        os.system("clear" if os.name == "posix" else "cls")

        if choice == 1:
            check_status()
        elif choice == 2:
            run_sync()
        elif choice == 3:
            msg = input(f"{C_YELLOW}Enter commit message: {C_RESET}").strip()
            run_sync(msg if msg else "Auto-sync")
        elif choice == 4:
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
        elif choice == 5:
            switch_folder()
        elif choice == 6:
            switch_push_method()
        elif choice == 7:
            change_directory()
        elif choice == 8:
            print(f"{C_CYAN}Goodbye!{C_RESET}")
            sys.exit()

        if choice not in [4, 8]:
            input(f"\n{C_YELLOW}Press ENTER to return to the menu...{C_RESET}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        print(f"{C_GREEN}Starting daemon mode. Running every hour...{C_RESET}")
        try:
            while True:
                run_sync("Auto-sync (Daemon)")
                time.sleep(3600)
        except Exception as e:
            print(f"{C_RED}Daemon crashed: {e}{C_RESET}")
    else:
        interactive_loop()
