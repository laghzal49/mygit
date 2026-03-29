import logging
import os
import re
import time

try:
    import github
    from github.GithubException import GithubException
    from git import Repo
    from git.exc import GitCommandError
    from dotenv import load_dotenv
except ImportError:
    github = None
    Repo = None
    GitCommandError = Exception
    GithubException = Exception

    def load_dotenv(*_args, **_kwargs):
        return False

ENV_PATH = os.path.expanduser("~/.mygit_tool/.env")
LOG_PATH = os.path.expanduser("~/.mygit_tool/mygit.log")

load_dotenv(ENV_PATH)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DESKTOP_PATH = os.path.abspath(
    os.path.expanduser(os.getenv("SCAN_PATH", "~/Desktop"))
)
PUSH_METHOD = os.getenv("PUSH_METHOD", "https").lower()
RETRY_COUNT = int(os.getenv("MYGIT_RETRY_COUNT", "3"))
RETRY_BACKOFF = float(os.getenv("MYGIT_RETRY_BACKOFF", "1.5"))
SELECTED_FOLDERS = []

C_CYAN = "\033[96m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_RESET = "\033[0m"


def setup_logger():
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    logger = logging.getLogger("mygit")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


LOGGER = setup_logger()


def log_info(message):
    LOGGER.info(message)


def log_error(message):
    LOGGER.error(message)


def emit_line(message, emit=print):
    if emit:
        emit(message)


def save_config():
    os.makedirs(os.path.dirname(ENV_PATH), exist_ok=True)
    with open(ENV_PATH, "w", encoding="utf-8") as env_file:
        if GITHUB_TOKEN:
            env_file.write(f"GITHUB_TOKEN={GITHUB_TOKEN}\n")
        env_file.write(f"SCAN_PATH={DESKTOP_PATH}\n")
        env_file.write(f"PUSH_METHOD={PUSH_METHOD}\n")
        env_file.write(f"MYGIT_RETRY_COUNT={RETRY_COUNT}\n")
        env_file.write(f"MYGIT_RETRY_BACKOFF={RETRY_BACKOFF}\n")


def set_scan_directory(path):
    global DESKTOP_PATH
    global SELECTED_FOLDERS

    DESKTOP_PATH = os.path.abspath(os.path.expanduser(path))
    SELECTED_FOLDERS = []
    save_config()
    log_info(f"Scan path changed to {DESKTOP_PATH}")


def set_token(token):
    global GITHUB_TOKEN

    GITHUB_TOKEN = token
    save_config()
    log_info("GitHub token updated")


def switch_push_method():
    global PUSH_METHOD

    PUSH_METHOD = "ssh" if PUSH_METHOD == "https" else "https"
    save_config()
    log_info(f"Push method switched to {PUSH_METHOD}")
    return PUSH_METHOD


def get_config_snapshot():
    return {
        "token_set": bool(GITHUB_TOKEN),
        "scan_path": DESKTOP_PATH,
        "push_method": PUSH_METHOD.upper(),
        "retry_count": RETRY_COUNT,
        "retry_backoff": RETRY_BACKOFF,
        "log_path": LOG_PATH,
    }


def get_clean_name(name):
    clean = re.sub(
        r"(?i)(^|[-_\s])git(?=$|[-_\s])",
        r"\1",
        name,
    )
    clean = re.sub(r"[-_\s]{2,}", "-", clean).strip(" -_")
    if not clean:
        return name.strip(" -_")
    return clean


def filter_folders_by_selection(folders, selected_folders):
    if not selected_folders:
        return folders

    selected_names = [folder[0] for folder in selected_folders]
    return [folder for folder in folders if folder[0] in selected_names]


def get_syncable_folders():
    valid_folders = []

    try:
        folder_names = os.listdir(DESKTOP_PATH)
    except OSError as exc:
        log_error(f"Cannot list scan directory {DESKTOP_PATH}: {exc}")
        return valid_folders

    for folder in folder_names:
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


def get_target_folders():
    folders = get_syncable_folders()
    return filter_folders_by_selection(folders, SELECTED_FOLDERS)


def retry_with_backoff(action_name, func, emit=print):
    last_error = None

    for attempt in range(1, RETRY_COUNT + 1):
        try:
            return func()
        except (
            GithubException,
            GitCommandError,
            OSError,
            TimeoutError,
        ) as exc:
            last_error = exc
            if attempt == RETRY_COUNT:
                break

            sleep_seconds = RETRY_BACKOFF * (2 ** (attempt - 1))
            emit_line(
                f"{action_name} failed ({attempt}/{RETRY_COUNT}). "
                f"Retrying in {sleep_seconds:.1f}s...",
                emit,
            )
            log_error(
                f"{action_name} failed on attempt {attempt}: {exc}. "
                f"Retrying in {sleep_seconds:.1f}s"
            )
            time.sleep(sleep_seconds)

    raise last_error


def get_or_create_remote_repo(user, clean_name, emit=print):
    try:
        return retry_with_backoff(
            f"Lookup repository {clean_name}",
            lambda: user.get_repo(clean_name),
            emit,
        )
    except GithubException as exc:
        if getattr(exc, "status", None) != 404:
            raise

    return retry_with_backoff(
        f"Create repository {clean_name}",
        lambda: user.create_repo(clean_name, private=True),
        emit,
    )


def ensure_origin_remote(repo, remote_url):
    if "origin" in [remote.name for remote in repo.remotes]:
        origin = repo.remote("origin")
        origin.set_url(remote_url)
        return origin

    return repo.create_remote("origin", remote_url)


def ensure_gitignore(path):
    gitignore_path = os.path.join(path, ".gitignore")
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, "w", encoding="utf-8") as gitignore_file:
            gitignore_file.write(
                "__pycache__/\nnode_modules/\n"
                ".DS_Store\n.env\nvenv/\n"
            )


def build_remote_url(gh_repo):
    if PUSH_METHOD == "ssh":
        return gh_repo.ssh_url
    return gh_repo.clone_url


def preview_sync_plan(commit_msg="Auto-sync", emit=print):
    emit_line("--- Dry Run Preview ---", emit)
    emit_line(f"Scan path: {DESKTOP_PATH}", emit)
    emit_line(f"Push method: {PUSH_METHOD.upper()}", emit)
    emit_line(f"Commit message: {commit_msg}", emit)

    folders = get_target_folders()
    if not folders:
        emit_line("No folders selected/available to sync.", emit)
        return []

    for folder, _ in folders:
        clean_name = get_clean_name(folder)
        emit_line(
            f"- {folder} -> repo `{clean_name}` | branch: main "
            f"| push: main:main",
            emit,
        )

    return folders


def check_status(emit=print):
    preview_sync_plan("Auto-sync", emit)


def run_sync(commit_msg="Auto-sync", show_preview=True, emit=print):
    if github is None or Repo is None:
        emit_line("Missing dependencies. Run poetry install.", emit)
        return

    if not GITHUB_TOKEN:
        emit_line("Error: GITHUB_TOKEN not found in .env", emit)
        return

    if show_preview:
        preview_sync_plan(commit_msg, emit)

    try:
        github_client = retry_with_backoff(
            "GitHub authentication",
            lambda: github.Github(auth=github.Auth.Token(GITHUB_TOKEN)),
            emit,
        )
        user = retry_with_backoff(
            "Fetch GitHub user",
            github_client.get_user,
            emit,
        )
    except Exception as exc:
        emit_line(f"GitHub Auth Error: {exc}", emit)
        log_error(f"GitHub Auth Error: {exc}")
        return

    folders = get_target_folders()
    if not folders:
        emit_line("No new folders to sync.", emit)
        return

    for folder, path in folders:
        clean_name = get_clean_name(folder)
        log_info(f"Processing folder {folder} -> {clean_name}")
        emit_line(f"Processing: {folder} -> {clean_name}", emit)

        try:
            repo = Repo.init(path)
            gh_repo = get_or_create_remote_repo(user, clean_name, emit)
            remote_url = build_remote_url(gh_repo)
            origin = ensure_origin_remote(repo, remote_url)

            ensure_gitignore(path)
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
                    retry_with_backoff(
                        f"Push {clean_name}",
                        lambda: origin.push(refspec="main:main"),
                        emit,
                    )
                finally:
                    origin.set_url(gh_repo.clone_url)
            else:
                retry_with_backoff(
                    f"Push {clean_name}",
                    lambda: origin.push(refspec="main:main"),
                    emit,
                )

            emit_line(
                f"Successfully pushed ({PUSH_METHOD.upper()}): {clean_name}",
                emit,
            )
            log_info(f"Sync success for {clean_name}")

        except GithubException as exc:
            error_data = getattr(exc, "data", {})
            error_message = (
                error_data.get("message", "")
                if isinstance(error_data, dict)
                else str(exc)
            )

            if (
                getattr(exc, "status", None) == 403
                and "Resource not accessible by personal access token"
                in error_message
            ):
                emit_line(
                    "GitHub token lacks permission to create repositories.",
                    emit,
                )
                log_error(
                    "Token lacks permission to create repositories "
                    f"for folder {folder}"
                )
                return

            emit_line(f"GitHub API error for {folder}: {exc}", emit)
            log_error(f"GitHub API error for {folder}: {exc}")
        except Exception as exc:
            emit_line(f"Error processing {folder}: {exc}", emit)
            log_error(f"Error processing {folder}: {exc}")
