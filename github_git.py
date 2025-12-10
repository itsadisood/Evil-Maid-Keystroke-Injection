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
            "content": content,
            "encoding": "utf-8",  # GitHub will hash it as a blob...i think?
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

    def can_reach_github():
        """Return True if GitHub API is reachable"""
        try:
            req = urllib.request.Request(
                "https://api.github.com",
                headers={"User-Agent": "GitHub-check"},
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=3):
                return True
        except Exception:
            return False

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

    def commit(self, message: str) -> str:
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

