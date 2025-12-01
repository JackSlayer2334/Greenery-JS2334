#!/usr/bin/env python3
import requests
import json
import os
import time

CONFIG_PATH = "config.json"
GRAPHQL_URL = "https://leetcode.com/graphql"

with open(CONFIG_PATH) as f:
    cfg = json.load(f)

USERNAME = cfg["leetcode_username"]
PRIMARY_LANG = cfg.get("primary_language", "cpp")

HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com",
    "User-Agent": "Mozilla/5.0"
}

# Map LeetCode lang -> file extension
LANG_EXT = {
    "cpp": "cpp",
    "c++": "cpp",
    "python": "py",
    "python3": "py",
    "java": "java",
    "javascript": "js",
    "c": "c"
}


def graphql(query: str, variables: dict):
    resp = requests.post(
        GRAPHQL_URL,
        headers=HEADERS,
        json={"query": query, "variables": variables},
        timeout=15
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL error: {data['errors']}")
    return data["data"]


def fetch_submission_list():
    """
    Paginate over all submissions for the user and yield accepted ones.
    """
    query = """
    query submissionList($username: String!, $offset: Int!, $limit: Int!) {
      submissionList(username: $username, offset: $offset, limit: $limit) {
        hasNext
        submissions {
          id
          statusDisplay
          lang
          titleSlug
          timestamp
        }
      }
    }
    """
    offset = 0
    limit = 20

    while True:
        data = graphql(query, {
            "username": USERNAME,
            "offset": offset,
            "limit": limit
        })["submissionList"]

        for sub in data["submissions"]:
            if sub["statusDisplay"] == "Accepted":
                yield sub

        if not data["hasNext"]:
            break
        offset += limit
        # Be nice to LeetCode
        time.sleep(0.5)


def fetch_submission_code(submission_id: int):
    """
    For a given submission id, fetch full code & more details.
    """
    query = """
    query submissionDetails($submissionId: Int!) {
      submissionDetails(submissionId: $submissionId) {
        id
        code
        lang
        runtime
        memory
        question {
          titleSlug
          title
        }
      }
    }
    """
    data = graphql(query, {"submissionId": submission_id})["submissionDetails"]
    return data


def main():
    os.makedirs("solutions", exist_ok=True)
    seen = set()  # last submission per question slug

    print(f"🔍 Fetching accepted submissions for {USERNAME} ...")
    for sub in fetch_submission_list():
        slug = sub["titleSlug"]
        if slug in seen:
            # We only keep the *latest* accepted submission per problem
            continue
        seen.add(slug)

        sid = int(sub["id"])
        print(f"  ➜ Fetching code for {slug} (submission {sid})")
        try:
            details = fetch_submission_code(sid)
        except Exception as e:
            print(f"    ⚠️ Failed to fetch code: {e}")
            continue

        lang = details["lang"].lower()
        ext = LANG_EXT.get(lang, LANG_EXT.get(PRIMARY_LANG, "txt"))

        folder = os.path.join("solutions", slug)
        os.makedirs(folder, exist_ok=True)

        file_path = os.path.join(folder, f"solution.{ext}")
        with open(file_path, "w") as f:
            f.write(details["code"])

        # Small sleep to avoid hammering API
        time.sleep(0.3)

    print("✅ Finished fetching submissions.")


if __name__ == "__main__":
    main()
