import json
import urllib.request
import urllib.error

TOKEN =  # Use a classic token not a fine grained one!


def main() -> None:
    url = "https://api.github.com/user"

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Python-Token-Test",
    }

    req = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode()
            print("STATUS:", resp.status)
            print("BODY:", body)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print("HTTP ERROR:", e.code, e.reason)
        print("BODY:", body)


if __name__ == "__main__":
    main()

