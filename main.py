import platform
import sys
import os


def detect_os( ) -> str:
    """
    Detect OS this script is being run on, 
    return either W for Windows, M for MacOS, L for Linux
    """
    system = platform.system()
    if system == "Windows": # Windows
        return "W"
    elif system == "Darwin": # MacOS
        return "M"
    elif system == "Linux": # Linux
        # Try to detect distro using /etc/os-release:
        # try:
        #     with open("/etc/os-release", "r") as f:
        #         data = f.read().lower()
        #         if "ubuntu" in data:
        #             return "Linux (Ubuntu)"
        #         elif "debian" in data:
        #             return "Linux (Debian)"
        #         elif "fedora" in data:
        #             return "Linux (Fedora)"
        #         elif "arch" in data:
        #             return "Linux (Arch)"
        #         elif "centos" in data:
        #             return "Linux (CentOS)"
        #         elif "alpine" in data:
        #             return "Linux (Alpine)"
        # except FileNotFoundError:
        #     pass

        # fallback
        return "L"
    # Ideally should never reach here and should be able to detect OS
    return "COULD_NOT_FIND_OS"


if __name__ == "__main__":
    # What is this supposed to do? 
    # It needs to start the program ? Figure out which mode to be in?
    # the mode needs to be figured out by the listener so key.py (logging/reading) keystrokes
    # figures out the mode
    #
    #
    # Something to control these:
    #
    # Attack mode: OS Dependent?
    # Sending mode:
    # Logging mode: Key.py (log keystrokes) [need to add OS Specific commands]


    # Detect the OS we are running on:
    print(detect_os())

    pass

