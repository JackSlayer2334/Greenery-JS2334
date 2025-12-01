#!/usr/bin/env python3
import requests
import json
import datetime

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


def fetch_stats():
    query = """
    query userProfile($username: String!) {
      matchedUser(username: $username) {
        submitStatsGlobal {
          acSubmissionNum {
            difficulty
            count
          }
        }
      }
    }
    """
    data = graphql(query, {"username": USERNAME})
    stats = data["matchedUser"]["submitStatsGlobal"]["acSubmissionNum"]

    # Expected order: ALL, EASY, MEDIUM, HARD
    counts = {item["difficulty"]: item["count"] for item in stats}
    total = counts.get("All", 0)
    easy = counts.get("Easy", 0)
    medium = counts.get("Medium", 0)
    hard = counts.get("Hard", 0)
    return total, easy, medium, hard


def main():
    total, easy, medium, hard = fetch_stats()
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    primary_label = {
        "cpp": "C++",
        "python": "Python",
        "java": "Java",
        "javascript": "JavaScript"
    }.get(PRIMARY_LANG.lower(), PRIMARY_LANG)

    readme = f"""# 🌸 𝐆𝐫𝐞𝐞𝐧𝐞𝐫𝐲-𝐉𝐒𝟐𝟑𝟑𝟒 🌸

> 🌱 *A LeetCode journey where each Accepted blooms into green.*

![Total Solved](https://img.shields.io/badge/Solved-{total}-blue)
![Easy](https://img.shields.io/badge/Easy-{easy}-brightgreen)
![Medium](https://img.shields.io/badge/Medium-{medium}-yellow)
![Hard](https://img.shields.io/badge/Hard-{hard}-red)
![Primary Lang](https://img.shields.io/badge/Language-{primary_label}-informational)

---

## ⚔️ Shinobi Status

- 👤 **User:** [{USERNAME}](https://leetcode.com/{USERNAME}/)
- 💻 **Primary Weapon:** `{primary_label}`
- 📚 **Total Problems Solved:** **{total}**
- 🟢 Easy: **{easy}**
- 🟡 Medium: **{medium}**
- 🔴 Hard: **{hard}**

🕒 **Last Synced:** `{ts}`

---

## 📁 Repository Layout

```bash
Greenery-JS2334/
│
├── solutions/
│   ├── two-sum/
│   │   ├── solution.cpp
│   │   └── README.md
│   ├── best-time-to-buy-and-sell-stock/
│   │   ├── solution.cpp
│   │   └── README.md
│   └── ...
│
├── fetch_leetcode.py      # Fetch accepted submissions
├── generate_readme.py     # Per-problem READMEs
├── stats.py               # This anime stats dashboard
├── push.sh                # Git auto-sync script
└── config.json            # Your settings"""