
import base64
import json
import os
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
            # Show GitHub's JSON error body so you know what's wrong
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
            "content": base64.b64encode(new_content.encode()).decode(),
        }
        url = f"{self.api}/contents/{path}"
        return self._request("PUT", url, payload)
