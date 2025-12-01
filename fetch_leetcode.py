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
    "authority": "leetcode.com",
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "origin": "https://leetcode.com",
    "referer": "https://leetcode.com",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "cookie": f"LEETCODE_SESSION={cfg['cookie']}"
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
    Fetch submissions using LeetCode REST API.
    Handles both old and new API formats.
    """
    submissions = []
    offset = 0

    while True:
        url = f"https://leetcode.com/api/submissions/?offset={offset}&limit=20"
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()

        # Support both formats
        submission_list = data.get("submissions") or data.get("submission_list")

        if not submission_list:
            print("⚠️ No submissions field found in response!")
            print("Response keys:", data.keys())
            break

        for sub in submission_list:
            if sub.get("status_display") == "Accepted":
                submissions.append({
                    "id": sub["id"],
                    "titleSlug": sub["title_slug"],
                    "lang": sub["lang"],
                })

        # new API uses has_next; old API used different patterns
        if not data.get("has_next", False):
            break

        offset += 20
        time.sleep(0.3)

    return submissions


def fetch_submission_code(submission_id: int):
    url = f"https://leetcode.com/submissions/detail/{submission_id}/"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    text = resp.text

    # Extract code from HTML
    start = text.find("submissionCode: '") + len("submissionCode: '")
    end = text.find("',\n  runtime", start)
    code = text[start:end].encode().decode('unicode_escape')

    # Extract language
    lang_start = text.find("getLangDisplay: '") + len("getLangDisplay: '")
    lang_end = text.find("',\n  memory", lang_start)
    lang = text[lang_start:lang_end]

    # Extract slug
    slug_start = text.find("questionTitleSlug: '") + len("questionTitleSlug: '")
    slug_end = text.find("',\n  title", slug_start)
    slug = text[slug_start:slug_end]

    return {"code": code, "lang": lang, "slug": slug}



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
