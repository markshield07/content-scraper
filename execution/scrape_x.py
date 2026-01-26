"""
X Account Scraper
Scrapes posts from target accounts for the last 12 hours.

Usage: python execution/scrape_x.py

Output: .tmp/scraped_{date}.json

Requires: APIFY_API_KEY in .env
"""

import os
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv(override=True)

# Configuration
TARGET_ACCOUNTS = [
    "TheCaliApe",
    "tboe3D",
    "Gratefulape",
    "MookieNFT",
]
HOURS_BACK = 12  # Scrape posts from last N hours

PROJECT_ROOT = Path(__file__).parent.parent
TMP_DIR = PROJECT_ROOT / ".tmp"

# Apify configuration - using xtdata Twitter scraper
# See https://apify.com/xtdata/twitter-x-scraper
APIFY_TOKEN = os.getenv("APIFY_API_KEY", "")
APIFY_ACTOR_ID = "xtdata~twitter-x-scraper"


def get_cutoff_time() -> datetime:
    """Get the cutoff time (12 hours ago)."""
    return datetime.now(timezone.utc) - timedelta(hours=HOURS_BACK)


def scrape_all_accounts(usernames: list[str], cutoff_time: datetime) -> list[dict]:
    """
    Scrape posts from all accounts in a single API call.
    More efficient and cheaper than individual calls.
    """
    if not APIFY_TOKEN:
        print("ERROR: APIFY_API_KEY not set")
        return []

    print(f"Scraping {len(usernames)} accounts via Apify...")

    # Build search queries for all users
    search_queries = [f"from:{username}" for username in usernames]

    # Start the actor run
    run_url = f"https://api.apify.com/v2/acts/{APIFY_ACTOR_ID}/runs"
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}

    # Actor-specific payload format for xtdata
    payload = {
        "searchTerms": search_queries,
        "maxItems": 50,
        "sort": "Latest",
    }

    try:
        # Start the run
        print("  Starting Apify actor...")
        response = requests.post(run_url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        run_data = response.json()
        run_id = run_data["data"]["id"]
        print(f"  Run ID: {run_id}")

        # Wait for completion (with timeout)
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
        max_wait = 180  # 3 minutes max
        waited = 0

        while waited < max_wait:
            time.sleep(10)
            waited += 10
            status_response = requests.get(status_url, headers=headers, timeout=30)
            status_data = status_response.json()
            status = status_data["data"]["status"]
            print(f"  Status: {status} ({waited}s)")

            if status == "SUCCEEDED":
                break
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                print(f"  Run failed: {status}")
                return []

        if waited >= max_wait:
            print("  Timeout waiting for results")
            return []

        # Get results
        dataset_id = status_data["data"]["defaultDatasetId"]
        results_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
        results_response = requests.get(results_url, headers=headers, timeout=30)
        raw_posts = results_response.json()

        print(f"  Retrieved {len(raw_posts)} raw results")

        # Filter and normalize posts
        posts = []
        skipped_empty = 0
        skipped_old = 0
        skipped_rt = 0

        for raw in raw_posts:
            # Skip empty results
            if raw.get("noResults"):
                skipped_empty += 1
                continue

            # Check for text in either field
            text_content = raw.get("full_text") or raw.get("text", "")
            if not text_content:
                skipped_empty += 1
                continue

            # Parse created_at timestamp
            created_str = (
                raw.get("created_at") or
                raw.get("createdAt") or
                raw.get("timestamp") or
                ""
            )
            try:
                if not created_str:
                    created_at = datetime.now(timezone.utc)
                elif "T" in str(created_str):
                    created_at = datetime.fromisoformat(str(created_str).replace("Z", "+00:00"))
                else:
                    # Twitter format: "Mon Jan 26 05:48:43 +0000 2026"
                    created_at = datetime.strptime(str(created_str), "%a %b %d %H:%M:%S %z %Y")
            except (ValueError, TypeError) as e:
                print(f"    Date parse error: {e} for '{created_str}'")
                created_at = datetime.now(timezone.utc)

            # Filter by time window
            if created_at < cutoff_time:
                skipped_old += 1
                continue

            # Extract username from the post
            author = raw.get("author", {})
            user = raw.get("user", {})
            username = (
                author.get("screen_name") or
                author.get("userName") or
                user.get("screen_name") or
                raw.get("username") or
                raw.get("screen_name") or
                "unknown"
            )

            # Normalize post format
            post = {
                "id": str(raw.get("id") or raw.get("id_str") or raw.get("tweetId", "")),
                "username": username,
                "text": raw.get("full_text") or raw.get("text", ""),
                "created_at": created_at.isoformat(),
                "likes": raw.get("likeCount") or raw.get("favorite_count") or raw.get("likes", 0),
                "retweets": raw.get("retweetCount") or raw.get("retweet_count") or raw.get("retweets", 0),
                "replies": raw.get("replyCount") or raw.get("reply_count") or raw.get("replies", 0),
                "media_urls": extract_media_urls(raw),
            }

            # Skip retweets
            if post["text"].startswith("RT @"):
                skipped_rt += 1
                continue

            posts.append(post)

        print(f"  Skipped: {skipped_empty} empty, {skipped_old} old, {skipped_rt} retweets")
        print(f"  Kept: {len(posts)} posts in time window")
        return posts

    except requests.RequestException as e:
        print(f"  Request failed: {e}")
        return []


def extract_media_urls(raw_post: dict) -> list[str]:
    """Extract media URLs from a post."""
    urls = []

    # Check for media in various possible locations
    media = (
        raw_post.get("media") or
        raw_post.get("entities", {}).get("media", []) or
        raw_post.get("extendedEntities", {}).get("media", []) or
        []
    )
    if isinstance(media, list):
        for item in media:
            if isinstance(item, dict):
                url = item.get("media_url_https") or item.get("url", "")
                if url:
                    urls.append(url)

    return urls


def save_results(posts: list[dict], date_str: str):
    """Save scraped posts to output file."""
    TMP_DIR.mkdir(exist_ok=True)
    output_file = TMP_DIR / f"scraped_{date_str}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(posts)} posts to {output_file}")
    return output_file


def main():
    print("=" * 50)
    print("X Account Scraper")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Window: Last {HOURS_BACK} hours")
    print("=" * 50)

    if not APIFY_TOKEN:
        print("\nERROR: APIFY_API_KEY not found in .env")
        print("Sign up at https://apify.com")
        print("Add APIFY_API_KEY=your_token to .env")
        exit(1)

    cutoff_time = get_cutoff_time()
    print(f"\nCutoff time: {cutoff_time.isoformat()}")
    print(f"Target accounts: {', '.join(['@' + a for a in TARGET_ACCOUNTS])}")

    # Scrape all accounts
    all_posts = scrape_all_accounts(TARGET_ACCOUNTS, cutoff_time)

    # Save results
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_file = save_results(all_posts, date_str)

    # Summary
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)

    by_account = {}
    for post in all_posts:
        username = post["username"]
        by_account[username] = by_account.get(username, 0) + 1

    for username, count in by_account.items():
        print(f"  @{username}: {count} posts")

    print(f"\nTotal: {len(all_posts)} posts")
    print(f"Output: {output_file}")

    if len(all_posts) == 0:
        print("\nWARNING: No posts scraped. Accounts may not have posted recently.")
        exit(0)  # Don't fail - might just be a quiet day

    print("\n" + "=" * 50)
    print("Scraping complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
