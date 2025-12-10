import pytest
from github_git import GitHubRepo, GitLike

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# ---------- GitHubRepo tests (mocking _request) ----------


def test_get_recent_commits_calls_correct_url(monkeypatch):
    calls = {}

    def fake_request(self, method, url, data=None):
        calls["method"] = method
        calls["url"] = url
        return [{"sha": "abc123", "commit": {"message": "test commit"}}]

    repo = GitHubRepo("owner", "repo", "dummy-token")

    monkeypatch.setattr(GitHubRepo, "_request", fake_request)

    commits = repo.get_recent_commits(limit=7)

    assert calls["method"] == "GET"
    assert calls["url"].endswith("/repos/owner/repo/commits?per_page=7")
    assert commits[0]["sha"] == "abc123"
    assert commits[0]["commit"]["message"] == "test commit"


def test_get_file_decodes_content_and_returns_sha(monkeypatch):
    def fake_request(self, method, url, data=None):
        import base64

        text = "hello world"
        encoded = base64.b64encode(text.encode()).decode()
        return {"content": encoded, "sha": "file-sha-123"}

    repo = GitHubRepo("owner", "repo", "dummy-token")
    monkeypatch.setattr(GitHubRepo, "_request", fake_request)

    content, sha = repo.get_file("path/to/file.txt")

    assert content == "hello world"
    assert sha == "file-sha-123"


def test_update_file_calls_put_with_correct_payload(monkeypatch):
    calls = {"get_file": None, "request": None}

    def fake_get_file(self, path):
        calls["get_file"] = path
        return ("old content", "old-sha-123")

    def fake_request(self, method, url, data=None):
        calls["request"] = {"method": method, "url": url, "data": data}
        return {"commit": {"sha": "new-commit-sha"}}

    repo = GitHubRepo("owner", "repo", "dummy-token")

    monkeypatch.setattr(GitHubRepo, "get_file", fake_get_file)
    monkeypatch.setattr(GitHubRepo, "_request", fake_request)

    result = repo.update_file("dir/file.txt", "new content", "update message")

    assert calls["get_file"] == "dir/file.txt"
    assert calls["request"]["method"] == "PUT"
    assert calls["request"]["url"].endswith(
        "/repos/owner/repo/contents/dir/file.txt"
    )
    payload = calls["request"]["data"]
    assert payload["message"] == "update message"
    assert "content" in payload
    assert payload["sha"] == "old-sha-123"
    assert result["commit"]["sha"] == "new-commit-sha"


def test_create_file_calls_put_with_correct_payload(monkeypatch):
    calls = {}

    def fake_request(self, method, url, data=None):
        calls["method"] = method
        calls["url"] = url
        calls["data"] = data
        return {
            "content": {"path": "newfile.txt"},
            "commit": {"sha": "commit-sha"},
        }

    repo = GitHubRepo("owner", "repo", "dummy-token")
    monkeypatch.setattr(GitHubRepo, "_request", fake_request)

    result = repo.create_file("newfile.txt", "file body", "add new file")

    assert calls["method"] == "PUT"
    assert calls["url"].endswith("/repos/owner/repo/contents/newfile.txt")
    payload = calls["data"]
    assert payload["message"] == "add new file"
    assert "content" in payload
    assert result["commit"]["sha"] == "commit-sha"


def test_low_level_git_helpers_call_correct_endpoints(monkeypatch):
    recorded = []

    def fake_request(self, method, url, data=None):
        recorded.append((method, url, data))
        if "/git/ref/heads/" in url:
            return {"object": {"sha": "head-sha"}}
        if "/git/commits/" in url and method == "GET":
            return {"tree": {"sha": "base-tree-sha"}}
        if url.endswith("/git/blobs"):
            return {"sha": "blob-sha"}
        if url.endswith("/git/trees"):
            return {"sha": "new-tree-sha"}
        if url.endswith("/git/commits") and method == "POST":
            return {"sha": "new-commit-sha"}
        if "/git/refs/heads/" in url and method == "PATCH":
            return {}
        return {}

    repo = GitHubRepo("owner", "repo", "dummy-token")
    monkeypatch.setattr(GitHubRepo, "_request", fake_request)

    head = repo.get_branch_head("main")
    assert head == "head-sha"

    commit_obj = repo.get_commit_obj("head-sha")
    assert commit_obj["tree"]["sha"] == "base-tree-sha"

    blob_sha = repo.create_blob("hello")
    assert blob_sha == "blob-sha"

    files = {"file1.txt": "aaa", "file2.txt": "bbb"}
    tree_sha = repo.create_tree("base-tree-sha", files)
    assert tree_sha == "new-tree-sha"

    commit_sha = repo.create_commit("msg", "new-tree-sha", ["head-sha"])
    assert commit_sha == "new-commit-sha"

    repo.update_branch_ref("main", "new-commit-sha")

    urls = [u for (_, u, _) in recorded]
    assert any("/git/ref/heads/main" in u for u in urls)
    assert any("/git/trees" in u for u in urls)
    assert any("/git/commits" in u for u in urls)
    assert any("/git/blobs" in u for u in urls)
    assert any("/git/refs/heads/main" in u for u in urls)


# ---------- GitLike tests (using a fake repo) ----------


class FakeRepo:
    # Fake repo implementing low-level methods used by GitLike,
    # so we can test GitLike.commit() without real network.

    def __init__(self):
        self.calls = []
        self.branch_heads = {"main": "head-sha-main"}
        self.commit_objs = {"head-sha-main": {"tree": {"sha": "base-tree-main"}}}
        self.created_trees = []
        self.created_commits = []
        self.updated_refs = []

    def get_branch_head(self, branch: str) -> str:
        self.calls.append(("get_branch_head", branch))
        return self.branch_heads[branch]

    def get_commit_obj(self, sha: str) -> dict:
        self.calls.append(("get_commit_obj", sha))
        return self.commit_objs[sha]

    def create_blob(self, content: str) -> str:
        self.calls.append(("create_blob", content))
        return f"blob-{len(content)}"

    def create_tree(self, base_tree_sha: str, files):
        files_copy = dict(files)
        self.calls.append(("create_tree", base_tree_sha, files_copy))
        self.created_trees.append((base_tree_sha, files_copy))
        return "new-tree-sha"

    def create_commit(self, message: str, tree_sha: str, parents):
        parents_copy = list(parents)
        self.calls.append(("create_commit", message, tree_sha, parents_copy))
        self.created_commits.append((message, tree_sha, parents_copy))
        return "new-commit-sha"

    def update_branch_ref(self, branch: str, new_sha: str, force: bool = False):
        self.calls.append(("update_branch_ref", branch, new_sha, force))
        self.updated_refs.append((branch, new_sha, force))


def test_gitlike_add_and_commit_multiple_files():
    fake_repo = FakeRepo()
    git = GitLike(fake_repo, branch="main")

    git.add("a.txt", "AAA")
    git.add("b.txt", "BBB")

    new_sha = git.commit_and_push("multi-file commit")

    assert new_sha == "new-commit-sha"
    assert git.last_commit() == "new-commit-sha"

    methods = [c[0] for c in fake_repo.calls]
    assert methods[0] == "get_branch_head"
    assert methods[1] == "get_commit_obj"
    assert "create_tree" in methods
    assert "create_commit" in methods
    assert "update_branch_ref" in methods

    base_tree_sha, files_in_tree = fake_repo.created_trees[0]
    assert base_tree_sha == "base-tree-main"
    assert files_in_tree["a.txt"] == "AAA"
    assert files_in_tree["b.txt"] == "BBB"

    branch, sha, force = fake_repo.updated_refs[0]
    assert branch == "main"
    assert sha == "new-commit-sha"
    assert force is False


def test_gitlike_commit_without_staging_raises():
    fake_repo = FakeRepo()
    git = GitLike(fake_repo, branch="main")

    with pytest.raises(RuntimeError):
        git.commit_and_push("should fail because nothing staged")

