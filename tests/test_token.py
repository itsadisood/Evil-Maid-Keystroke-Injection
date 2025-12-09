
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from github_git import GitHubRepo, GitLike
import json
import urllib.request
import urllib.error

TOKEN = "" # Use a classic token not a fine grained one!

def demo_multi_file_commit() -> None:
    # Use a classic token not a fine grained one!
    token = "" # rrlyy should swap to os.getenv("GITHUB_TOKEN") but eh

    repo = GitHubRepo("Alishah634", "HID_Command_Control_Server", token)

    git = GitLike(repo, branch="main")

    # Stage multiple files
    git.add("logs/keys.txt", "keystroke data here\n")
    git.add("logs/meta.json", '{"device": "usb-armory", "status": "ok"}\n')
    git.add("README_fragment.md", "Updated via Python multi-file commit\n")

    # One commit that includes *all* three files
    new_sha = git.commit("Add logs and README fragment from device")
    print("Created commit:", new_sha)

def main() -> None:
    # url = "https://api.github.com/user"
    #
    # headers = {
    #     "Accept": "application/vnd.github+json",
    #     "Authorization": f"Bearer {TOKEN}",
    #     "X-GitHub-Api-Version": "2022-11-28",
    #     "User-Agent": "Python-Token-Test",
    # }
    #
    # req = urllib.request.Request(url, headers=headers, method="GET")
    #
    # try:
    #     with urllib.request.urlopen(req) as resp:
    #         body = resp.read().decode()
    #         print("STATUS:", resp.status)
    #         print("BODY:", body)
    # except urllib.error.HTTPError as e:
    #     body = e.read().decode()
    #     print("HTTP ERROR:", e.code, e.reason)
    #     print("BODY:", body)
    #
    demo_multi_file_commit()

if __name__ == "__main__":
    main()

