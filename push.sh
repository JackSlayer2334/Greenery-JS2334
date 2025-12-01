#!/bin/bash

# Exit on error
set -e

# Go to repo directory (script location)
cd "$(dirname "$0")"

echo "🌱 Running Greenery-JS2334 sync..."

# 1) Fetch latest accepted solutions
python3 fetch_leetcode.py

# 2) Generate per-problem READMEs
python3 generate_readme.py

# 3) Update root README stats
python3 stats.py

# 4) Git add / commit / push
git add .

# Check if there are changes
if git diff-index --quiet HEAD --; then
    echo "No changes to commit. 🌿"
    exit 0
fi

COMMIT_MSG="auto-sync $(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "$COMMIT_MSG"
git push origin main

echo "✅ Sync complete & pushed to GitHub."
