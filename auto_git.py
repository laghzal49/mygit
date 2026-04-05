import sys
import time

import mygit_core as core
from mygit_ui import interactive_loop


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        print(f"{
            core.C_GREEN}Starting daemon mode. Running every hour...{
                core.C_RESET}")
        core.log_info("Daemon mode started")
        try:
            while True:
                core.run_sync("Auto-sync (Daemon)", show_preview=False)
                time.sleep(3600)
        except Exception as exc:
            print(f"{core.C_RED}Daemon crashed: {exc}{core.C_RESET}")
            core.log_error(f"Daemon crashed: {exc}")
    else:
        interactive_loop()


if __name__ == "__main__":
    main()
