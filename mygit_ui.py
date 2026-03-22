import curses
import os
import sys
import time

import mygit_core as core


def init_colors():
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)


def curses_text_input(stdscr, title, prompt, initial_value=""):
    curses.echo()
    value = initial_value
    max_width = 52

    while True:
        stdscr.clear()
        stdscr.addstr(1, 2, "╔════════════════════════════════════════════════════╗", curses.color_pair(1))
        stdscr.addstr(2, 2, f"║ {title[:50].ljust(50)} ║", curses.color_pair(1))
        stdscr.addstr(3, 2, "╠════════════════════════════════════════════════════╣", curses.color_pair(1))
        stdscr.addstr(5, 4, prompt[:50], curses.color_pair(2))
        stdscr.addstr(7, 4, "Input:", curses.color_pair(1))
        stdscr.addstr(7, 11, value[:max_width].ljust(max_width), curses.color_pair(3))
        stdscr.addstr(20, 2, "ENTER: confirm | ESC: cancel", curses.color_pair(2))
        stdscr.refresh()

        stdscr.move(7, 11 + min(len(value), max_width - 1))
        key = stdscr.getch()

        if key in [27]:
            curses.noecho()
            return None
        if key in [curses.KEY_ENTER, 10, 13]:
            curses.noecho()
            return value.strip()
        if key in [curses.KEY_BACKSPACE, 127, 8]:
            value = value[:-1]
        elif 32 <= key <= 126 and len(value) < max_width:
            value += chr(key)


def curses_text_view(stdscr, title, lines):
    current_row = 0
    max_visible = 14

    if not lines:
        lines = ["(no output)"]

    while True:
        stdscr.clear()
        stdscr.addstr(1, 2, "╔════════════════════════════════════════════════════╗", curses.color_pair(1))
        stdscr.addstr(2, 2, f"║ {title[:50].ljust(50)} ║", curses.color_pair(1))
        stdscr.addstr(3, 2, "╠════════════════════════════════════════════════════╣", curses.color_pair(1))

        for idx in range(max_visible):
            line_index = current_row + idx
            if line_index >= len(lines):
                break
            stdscr.addstr(5 + idx, 4, str(lines[line_index])[:46], curses.color_pair(1))

        stdscr.addstr(20, 2, "↑/↓ scroll | ENTER/ESC close", curses.color_pair(2))
        stdscr.refresh()

        key = stdscr.getch()
        if key in [27, curses.KEY_ENTER, 10, 13]:
            return
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < max(0, len(lines) - max_visible):
            current_row += 1


def run_action_with_capture(stdscr, title, action):
    lines = []
    action(lambda message: lines.append(str(message)))
    curses_text_view(stdscr, title, lines)


def browse_directory_curses(stdscr, start_path):
    current_path = os.path.abspath(os.path.expanduser(start_path))
    current_row = 0
    offset = 0
    max_visible = 12

    while True:
        try:
            entries = sorted(
                [
                    entry
                    for entry in os.listdir(current_path)
                    if os.path.isdir(os.path.join(current_path, entry))
                    and not entry.startswith('.')
                ]
            )
        except OSError:
            entries = []

        menu_items = ["[Use this directory]", "[.. parent]"] + entries

        if current_row >= len(menu_items):
            current_row = max(0, len(menu_items) - 1)

        stdscr.clear()
        stdscr.addstr(1, 2, "╔════════════════════════════════════════════════════╗", curses.color_pair(1))
        stdscr.addstr(2, 2, "║ 📂 Browse Scan Directory                           ║", curses.color_pair(1))
        stdscr.addstr(3, 2, "╠════════════════════════════════════════════════════╣", curses.color_pair(1))
        stdscr.addstr(4, 4, current_path[:50], curses.color_pair(2))

        if current_row < offset:
            offset = current_row
        elif current_row >= offset + max_visible:
            offset = current_row - max_visible + 1

        for view_index in range(max_visible):
            item_index = offset + view_index
            if item_index >= len(menu_items):
                break
            y_pos = 6 + view_index
            text = menu_items[item_index][:46]
            if item_index == current_row:
                stdscr.addstr(y_pos, 4, text.ljust(46), curses.color_pair(3))
            else:
                stdscr.addstr(y_pos, 4, text.ljust(46), curses.color_pair(1))

        stdscr.addstr(20, 2, "ENTER: open/select | ESC: cancel", curses.color_pair(2))
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu_items) - 1:
            current_row += 1
        elif key in [27]:
            return None
        elif key in [curses.KEY_ENTER, 10, 13]:
            selected = menu_items[current_row]
            if selected == "[Use this directory]":
                return current_path
            if selected == "[.. parent]":
                current_path = os.path.dirname(current_path)
                current_row = 0
                offset = 0
            else:
                current_path = os.path.join(current_path, selected)
                current_row = 0
                offset = 0


def curses_change_directory(stdscr):
    options = ["Browse directories", "Enter path manually", "Cancel"]
    current_row = 0

    while True:
        stdscr.clear()
        stdscr.addstr(1, 2, "╔════════════════════════════════════════════════════╗", curses.color_pair(1))
        stdscr.addstr(2, 2, "║ 📂 Change Scan Directory                           ║", curses.color_pair(1))
        stdscr.addstr(3, 2, "╠════════════════════════════════════════════════════╣", curses.color_pair(1))
        stdscr.addstr(4, 4, f"Current: {core.DESKTOP_PATH}"[:50], curses.color_pair(2))

        for index, option in enumerate(options):
            y_pos = 7 + index
            if index == current_row:
                stdscr.addstr(y_pos, 4, option.ljust(46), curses.color_pair(3))
            else:
                stdscr.addstr(y_pos, 4, option.ljust(46), curses.color_pair(1))

        stdscr.addstr(20, 2, "ENTER: select | ESC: back", curses.color_pair(2))
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(options) - 1:
            current_row += 1
        elif key in [27]:
            return
        elif key in [curses.KEY_ENTER, 10, 13]:
            selected_option = options[current_row]

            if selected_option == "Browse directories":
                new_path = browse_directory_curses(stdscr, core.DESKTOP_PATH)
            elif selected_option == "Enter path manually":
                new_path = curses_text_input(
                    stdscr,
                    "Manual Path Entry",
                    "Type full path:",
                    core.DESKTOP_PATH,
                )
            else:
                return

            if new_path is None:
                continue

            expanded_path = os.path.abspath(os.path.expanduser(new_path))
            if not os.path.isdir(expanded_path):
                curses_text_view(stdscr, "Invalid Directory", ["Path does not exist or is not a folder."])
                continue

            core.set_scan_directory(expanded_path)
            curses_text_view(stdscr, "Directory Updated", [f"New scan path: {core.DESKTOP_PATH}"])
            return


def curses_switch_folder(stdscr):
    folders = core.get_syncable_folders()
    if not folders:
        curses_text_view(stdscr, "Folder Selection", ["No available folders to select right now."])
        return

    current_row = 0
    offset = 0
    max_visible = 12

    selected_names = [folder[0] for folder in core.SELECTED_FOLDERS]
    selected_indices = {
        index
        for index, folder_info in enumerate(folders)
        if folder_info[0] in selected_names
    }

    while True:
        stdscr.clear()
        stdscr.addstr(1, 2, "╔════════════════════════════════════════════════════╗", curses.color_pair(1))
        stdscr.addstr(2, 2, "║ 📁 SELECT FOLDERS (SPACE to toggle, ENTER to save) ║", curses.color_pair(1))
        stdscr.addstr(3, 2, "╠════════════════════════════════════════════════════╣", curses.color_pair(1))

        if current_row < offset:
            offset = current_row
        elif current_row >= offset + max_visible:
            offset = current_row - max_visible + 1

        for view_index in range(max_visible):
            folder_index = offset + view_index
            if folder_index >= len(folders):
                break

            folder_name = folders[folder_index][0]
            y_pos = 4 + view_index
            is_selected = folder_index in selected_indices
            checkbox = "[X]" if is_selected else "[ ]"
            display_text = f"{checkbox} {folder_name}"

            if folder_index == current_row:
                stdscr.addstr(y_pos, 4, display_text.ljust(46), curses.color_pair(3))
            else:
                color = curses.color_pair(2) if is_selected else curses.color_pair(1)
                stdscr.addstr(y_pos, 4, display_text.ljust(46), color)

        stdscr.addstr(17, 2, "╚════════════════════════════════════════════════════╝", curses.color_pair(1))
        stdscr.addstr(19, 2, "Arrows to move | SPACE to toggle | ENTER to confirm", curses.color_pair(2))
        stdscr.addstr(20, 2, "ESC or 'q' to cancel", curses.color_pair(1))
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(folders) - 1:
            current_row += 1
        elif key == ord(' '):
            if current_row in selected_indices:
                selected_indices.remove(current_row)
            else:
                selected_indices.add(current_row)
        elif key in [curses.KEY_ENTER, 10, 13]:
            core.SELECTED_FOLDERS = [folders[index] for index in selected_indices]
            return
        elif key in [27, ord('q')]:
            return


def curses_config_menu(stdscr):
    options = [
        "Update GitHub Token",
        "Switch Push Method",
        "Change Scan Directory",
        "Show Current Config",
        "Back",
    ]
    current_row = 0

    while True:
        stdscr.clear()
        stdscr.addstr(1, 2, "╔════════════════════════════════════════════════════╗", curses.color_pair(1))
        stdscr.addstr(2, 2, "║ ⚙️ CONFIG MENU                                     ║", curses.color_pair(1))
        stdscr.addstr(3, 2, "╠════════════════════════════════════════════════════╣", curses.color_pair(1))

        for index, option in enumerate(options):
            y_pos = 6 + index
            if index == current_row:
                stdscr.addstr(y_pos, 4, option.ljust(46), curses.color_pair(3))
            else:
                stdscr.addstr(y_pos, 4, option.ljust(46), curses.color_pair(1))

        stdscr.addstr(20, 2, "ENTER: select | ESC: back", curses.color_pair(2))
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(options) - 1:
            current_row += 1
        elif key in [27]:
            return
        elif key in [curses.KEY_ENTER, 10, 13]:
            selected = options[current_row]

            if selected == "Update GitHub Token":
                new_token = curses_text_input(stdscr, "Update GitHub Token", "Paste new token:", "")
                if new_token:
                    core.set_token(new_token)
                    curses_text_view(stdscr, "Token Updated", ["GitHub token saved successfully."])
            elif selected == "Switch Push Method":
                method = core.switch_push_method().upper()
                curses_text_view(stdscr, "Push Method Updated", [f"Now using: {method}"])
            elif selected == "Change Scan Directory":
                curses_change_directory(stdscr)
            elif selected == "Show Current Config":
                cfg = core.get_config_snapshot()
                lines = [
                    f"Token: {'set' if cfg['token_set'] else 'missing'}",
                    f"Scan path: {cfg['scan_path']}",
                    f"Push method: {cfg['push_method']}",
                    f"Retry count: {cfg['retry_count']}",
                    f"Retry backoff: {cfg['retry_backoff']}",
                    f"Log path: {cfg['log_path']}",
                ]
                curses_text_view(stdscr, "Current Config", lines)
            else:
                return


def run_background_loop_curses(stdscr):
    logs = ["Background loop started. Press q to stop."]
    next_run = time.time()

    while True:
        now = time.time()
        if now >= next_run:
            run_logs = []
            core.run_sync("Auto-sync", show_preview=False, emit=run_logs.append)
            if run_logs:
                logs.extend(run_logs)
            else:
                logs.append("No output from sync cycle.")
            next_run = now + 3600

        stdscr.clear()
        stdscr.addstr(1, 2, "╔════════════════════════════════════════════════════╗", curses.color_pair(1))
        stdscr.addstr(2, 2, "║ 🔄 BACKGROUND LOOP                                 ║", curses.color_pair(1))
        stdscr.addstr(3, 2, "╠════════════════════════════════════════════════════╣", curses.color_pair(1))

        recent = logs[-12:]
        for idx, line in enumerate(recent):
            stdscr.addstr(5 + idx, 4, line[:46], curses.color_pair(1))

        remaining = max(0, int(next_run - now))
        stdscr.addstr(19, 2, f"Next run in: {remaining}s"[:50], curses.color_pair(2))
        stdscr.addstr(20, 2, "Press q to stop loop", curses.color_pair(2))
        stdscr.refresh()

        stdscr.timeout(1000)
        key = stdscr.getch()
        if key in [ord('q'), 27]:
            return


def curses_menu(stdscr):
    init_colors()

    menu_items = [
        "📊 Check Status (Dry Run)",
        "⚡ Run Auto-Sync Now",
        "📝 Run Sync with Custom Commit",
        "🔄 Start Background Loop (1hr)",
        "📁 Switch Folders (Multi-Select)",
        "🔀 Switch Push Method (SSH/HTTPS)",
        "📂 Change Scan Directory",
        "⚙️ Config (Token/Path/Push)",
        "❌ Exit",
    ]
    descriptions = [
        "Preview folders/repo names that would sync (dry run).",
        "Run immediate sync for current selection.",
        "Run sync with your custom commit message.",
        "Keep syncing every hour until stopped.",
        "Choose one or multiple folders to target.",
        "Toggle remote auth mode between HTTPS and SSH.",
        "Change scan path (browse like VS Code or type path).",
        "Edit token, push mode, and path settings.",
        "Exit application.",
    ]

    current_row = 0

    while True:
        stdscr.clear()

        if not core.SELECTED_FOLDERS:
            selected_name = "All folders"
        else:
            names = [folder[0] for folder in core.SELECTED_FOLDERS]
            selected_name = ", ".join(names)
            if len(selected_name) > 35:
                selected_name = f"{len(names)} folders selected"

        stdscr.addstr(1, 2, "╔════════════════════════════════════════════════════╗", curses.color_pair(1))
        stdscr.addstr(2, 2, "║ 🚀 MYGIT AUTOMATION · CURSUS TUI                   ║", curses.color_pair(1))
        stdscr.addstr(3, 2, "╠════════════════════════════════════════════════════╣", curses.color_pair(1))
        stdscr.addstr(4, 2, f"║ Scan path : {core.DESKTOP_PATH:<38} ║", curses.color_pair(1))
        stdscr.addstr(5, 2, f"║ Push mode : {core.PUSH_METHOD.upper():<38} ║", curses.color_pair(1))
        stdscr.addstr(6, 2, f"║ Selected  : {selected_name:<38} ║", curses.color_pair(1))
        stdscr.addstr(7, 2, "╠════════════════════════════════════════════════════╣", curses.color_pair(1))

        for index, item in enumerate(menu_items):
            y_pos = 9 + index
            if index == current_row:
                stdscr.addstr(y_pos, 4, item.ljust(46), curses.color_pair(3))
            else:
                stdscr.addstr(y_pos, 4, item.ljust(46), curses.color_pair(1))

        stdscr.addstr(19, 2, "╚════════════════════════════════════════════════════╝", curses.color_pair(1))
        stdscr.addstr(21, 2, descriptions[current_row][:50], curses.color_pair(2))
        stdscr.addstr(22, 2, "Use ↑/↓ arrows to navigate, ENTER to select.", curses.color_pair(2))
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(menu_items) - 1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:
            return current_row + 1


def interactive_loop():
    while True:
        choice = curses.wrapper(curses_menu)

        if choice == 1:
            curses.wrapper(
                lambda stdscr: run_action_with_capture(
                    stdscr,
                    "Dry Run Preview",
                    lambda emit: core.check_status(emit=emit),
                )
            )
        elif choice == 2:
            curses.wrapper(
                lambda stdscr: run_action_with_capture(
                    stdscr,
                    "Run Auto-Sync",
                    lambda emit: core.run_sync(show_preview=True, emit=emit),
                )
            )
        elif choice == 3:
            commit_message = curses.wrapper(
                lambda stdscr: curses_text_input(
                    stdscr,
                    "Custom Commit Message",
                    "Enter commit message:",
                    "Auto-sync",
                )
            )
            if commit_message is None:
                continue
            commit_message = commit_message or "Auto-sync"
            curses.wrapper(
                lambda stdscr: run_action_with_capture(
                    stdscr,
                    "Run Custom Commit Sync",
                    lambda emit: core.run_sync(
                        commit_msg=commit_message,
                        show_preview=True,
                        emit=emit,
                    ),
                )
            )
        elif choice == 4:
            curses.wrapper(run_background_loop_curses)
        elif choice == 5:
            curses.wrapper(curses_switch_folder)
        elif choice == 6:
            method = core.switch_push_method().upper()
            curses.wrapper(
                lambda stdscr: curses_text_view(
                    stdscr,
                    "Push Method Updated",
                    [f"Now using: {method}"],
                )
            )
        elif choice == 7:
            curses.wrapper(curses_change_directory)
        elif choice == 8:
            curses.wrapper(curses_config_menu)
        elif choice == 9:
            print(f"{core.C_CYAN}Goodbye!{core.C_RESET}")
            sys.exit()
