"""
Voice Analysis Script
Scrapes @KRAM_btc posts and extracts voice/style patterns.

Usage: python execution/analyze_voice.py

Output: Updates directives/voice_profile.md with extracted patterns

Note: Uses Apify Twitter Scraper API (free tier available)
      Sign up at https://apify.com and get your API token
"""

import os
import json
import re
import time
from datetime import datetime
from pathlib import Path
from collections import Counter
from dotenv import load_dotenv

try:
    import requests
except ImportError:
    print("Please install requests: pip install requests")
    exit(1)

# Load environment variables
load_dotenv()

# Configuration
USERNAME = "KRAM_btc"
MAX_POSTS = 100  # Number of posts to analyze
PROJECT_ROOT = Path(__file__).parent.parent
TMP_DIR = PROJECT_ROOT / ".tmp"
VOICE_PROFILE_PATH = PROJECT_ROOT / "directives" / "voice_profile.md"

# Apify configuration
APIFY_TOKEN = os.getenv("APIFY_API_KEY", "")
APIFY_ACTOR_ID = "shanes~tweet-flash"  # Lightweight Twitter scraper


def scrape_with_apify(username: str, max_posts: int = 100) -> list[dict]:
    """
    Scrape posts using Apify Twitter Scraper.
    Requires APIFY_API_KEY in .env file.
    """
    if not APIFY_TOKEN:
        print("APIFY_API_KEY not found in .env file")
        print("Sign up at https://apify.com (free tier available)")
        print("Add APIFY_API_KEY=your_token to .env file")
        return []

    print(f"Scraping @{username} via Apify...")

    # Start the actor run
    run_url = f"https://api.apify.com/v2/acts/{APIFY_ACTOR_ID}/runs"
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    payload = {
        "searchTerms": [f"from:{username}"],
        "maxTweets": max_posts,
    }

    try:
        # Start the run
        response = requests.post(run_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        run_data = response.json()
        run_id = run_data["data"]["id"]
        print(f"Started Apify run: {run_id}")

        # Wait for completion
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"
        for _ in range(60):  # Wait up to 5 minutes
            time.sleep(5)
            status_response = requests.get(status_url, headers=headers, timeout=30)
            status_data = status_response.json()
            status = status_data["data"]["status"]
            print(f"  Status: {status}")

            if status == "SUCCEEDED":
                break
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                print(f"Run failed with status: {status}")
                return []

        # Get results
        dataset_id = status_data["data"]["defaultDatasetId"]
        results_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
        results_response = requests.get(results_url, headers=headers, timeout=30)
        posts = results_response.json()

        print(f"Retrieved {len(posts)} posts")
        return posts

    except requests.RequestException as e:
        print(f"Apify request failed: {e}")
        return []


def scrape_with_nitter(username: str, max_posts: int = 100) -> list[dict]:
    """
    Fallback: Scrape posts using public Nitter instances.
    No API key required but less reliable.
    """
    # List of public Nitter instances (these change frequently)
    nitter_instances = [
        "nitter.privacydev.net",
        "nitter.poast.org",
        "nitter.bird.froth.zone",
    ]

    print(f"Attempting Nitter scrape for @{username}...")

    for instance in nitter_instances:
        try:
            url = f"https://{instance}/{username}/rss"
            response = requests.get(url, timeout=15, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })

            if response.status_code == 200:
                # Parse RSS feed
                from xml.etree import ElementTree
                root = ElementTree.fromstring(response.content)

                posts = []
                for item in root.findall(".//item")[:max_posts]:
                    title = item.find("title")
                    description = item.find("description")
                    pub_date = item.find("pubDate")

                    if title is not None or description is not None:
                        text = description.text if description is not None else title.text
                        # Clean HTML
                        text = re.sub(r"<[^>]+>", "", text or "")

                        posts.append({
                            "text": text,
                            "created_at": pub_date.text if pub_date is not None else "",
                        })

                if posts:
                    print(f"Retrieved {len(posts)} posts from {instance}")
                    return posts

        except Exception as e:
            print(f"  {instance} failed: {e}")
            continue

    print("All Nitter instances failed")
    return []


def load_sample_posts() -> list[dict]:
    """
    Fallback: Load sample posts if scraping fails.
    User can manually add posts to .tmp/sample_posts.json
    """
    sample_file = TMP_DIR / "sample_posts.json"

    if sample_file.exists():
        print(f"Loading sample posts from {sample_file}")
        with open(sample_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # Create template file for user to fill in
    TMP_DIR.mkdir(exist_ok=True)
    template = [
        {"text": "Paste your tweet text here", "created_at": "2024-01-01"},
        {"text": "Add more examples...", "created_at": "2024-01-02"},
    ]
    with open(sample_file, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)

    print(f"\nScraping failed. Please manually add your posts to:")
    print(f"  {sample_file}")
    print("Then re-run this script.")

    return []


def scrape_user_posts(username: str, max_posts: int = 100) -> list[dict]:
    """
    Main scraping function - tries multiple methods.
    """
    TMP_DIR.mkdir(exist_ok=True)
    output_file = TMP_DIR / f"{username}_posts.json"

    # Try Apify first (most reliable)
    posts = scrape_with_apify(username, max_posts)

    # Fallback to Nitter
    if not posts:
        posts = scrape_with_nitter(username, max_posts)

    # Fallback to manual sample file
    if not posts:
        posts = load_sample_posts()

    # Save whatever we got
    if posts:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(posts, f, indent=2, default=str)
        print(f"Saved posts to {output_file}")

    return posts


def extract_text_content(posts: list[dict]) -> list[str]:
    """Extract just the text content from posts."""
    texts = []
    for post in posts:
        # Handle different field names from different sources
        text = (
            post.get("text") or
            post.get("content") or
            post.get("rawContent") or
            post.get("full_text") or
            ""
        )
        if text:
            # Clean up - remove URLs for analysis
            text_clean = re.sub(r"https?://\S+", "", text).strip()
            if text_clean:
                texts.append(text_clean)
    return texts


def analyze_tone(texts: list[str]) -> dict:
    """Analyze tone patterns in the posts."""
    analysis = {
        "uses_caps": 0,
        "uses_emoji": 0,
        "uses_hashtags": 0,
        "uses_mentions": 0,
        "avg_length": 0,
        "question_posts": 0,
        "exclamation_posts": 0,
    }

    total = len(texts)
    if total == 0:
        return analysis

    total_length = 0

    for text in texts:
        total_length += len(text)

        # Check for all caps words (excitement)
        if re.search(r"\b[A-Z]{2,}\b", text):
            analysis["uses_caps"] += 1

        # Check for emojis
        if re.search(r"[\U0001F300-\U0001F9FF]", text):
            analysis["uses_emoji"] += 1

        # Hashtags
        if "#" in text:
            analysis["uses_hashtags"] += 1

        # Mentions
        if "@" in text:
            analysis["uses_mentions"] += 1

        # Questions
        if "?" in text:
            analysis["question_posts"] += 1

        # Exclamations
        if "!" in text:
            analysis["exclamation_posts"] += 1

    analysis["avg_length"] = total_length // total

    # Convert to percentages
    for key in ["uses_caps", "uses_emoji", "uses_hashtags", "uses_mentions", "question_posts", "exclamation_posts"]:
        analysis[key] = f"{(analysis[key] / total) * 100:.0f}%"

    return analysis


def extract_common_phrases(texts: list[str], min_words: int = 2, max_words: int = 4) -> list[str]:
    """Extract commonly used phrases."""
    phrase_counter = Counter()

    for text in texts:
        # Normalize
        text_lower = text.lower()
        words = re.findall(r"\b\w+\b", text_lower)

        # Extract n-grams
        for n in range(min_words, max_words + 1):
            for i in range(len(words) - n + 1):
                phrase = " ".join(words[i:i+n])
                # Filter out common stopword-only phrases
                stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "to", "of", "and", "in", "that", "it", "for", "on", "with"}
                phrase_words = set(phrase.split())
                if not phrase_words.issubset(stopwords):
                    phrase_counter[phrase] += 1

    # Return phrases that appear more than once
    common = [phrase for phrase, count in phrase_counter.most_common(20) if count > 1]
    return common[:10]


def extract_topics(texts: list[str]) -> list[str]:
    """Extract main topics/themes from posts."""
    # Common crypto/NFT/Web3 keywords to look for
    topic_keywords = {
        "nft": ["nft", "nfts", "mint", "minted", "collection", "pfp"],
        "crypto": ["crypto", "bitcoin", "btc", "eth", "ethereum", "token", "coin"],
        "trading": ["buy", "sell", "trade", "trading", "pump", "dump", "bullish", "bearish"],
        "community": ["gm", "wagmi", "ngmi", "fam", "community", "apes", "frens"],
        "art": ["art", "artist", "create", "creative", "design"],
        "defi": ["defi", "yield", "stake", "staking", "apy"],
        "gaming": ["game", "gaming", "play", "metaverse"],
        "culture": ["irl", "vibes", "mood", "energy", "based"],
    }

    topic_counts = Counter()
    all_text = " ".join(texts).lower()

    for topic, keywords in topic_keywords.items():
        for keyword in keywords:
            count = len(re.findall(rf"\b{keyword}\b", all_text))
            topic_counts[topic] += count

    # Return topics that have mentions
    topics = [topic for topic, count in topic_counts.most_common() if count > 0]
    return topics


def select_example_posts(posts: list[dict], count: int = 5) -> list[str]:
    """Select the best example posts (highest engagement or most representative)."""
    # Sort by engagement if available
    def get_engagement(post):
        return (
            post.get("likeCount", 0) or post.get("favorite_count", 0) +
            post.get("retweetCount", 0) or post.get("retweet_count", 0) +
            post.get("replyCount", 0) or post.get("reply_count", 0)
        )

    sorted_posts = sorted(posts, key=get_engagement, reverse=True)

    examples = []
    for post in sorted_posts[:count * 2]:  # Get more than needed to filter
        text = (
            post.get("text") or
            post.get("content") or
            post.get("rawContent") or
            post.get("full_text") or
            ""
        )
        # Skip very short posts or retweets
        if text and len(text) > 20 and not text.startswith("RT @"):
            examples.append(text)
            if len(examples) >= count:
                break

    return examples


def update_voice_profile(analysis: dict, phrases: list, topics: list, examples: list):
    """Update the voice profile markdown file with extracted data."""

    # Read current file
    with open(VOICE_PROFILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Build the voice characteristics section
    tone_section = f"""### Tone
- Average post length: {analysis['avg_length']} characters
- Uses ALL CAPS for emphasis: {analysis['uses_caps']} of posts
- Uses emojis: {analysis['uses_emoji']} of posts
- Uses hashtags: {analysis['uses_hashtags']} of posts
- Mentions others: {analysis['uses_mentions']} of posts
- Asks questions: {analysis['question_posts']} of posts
- Uses exclamations: {analysis['exclamation_posts']} of posts"""

    phrases_section = "### Common Phrases\n" + "\n".join([f"- \"{phrase}\"" for phrase in phrases]) if phrases else "### Common Phrases\n- (No distinct phrases detected)"

    topics_section = "### Topics\n" + "\n".join([f"- {topic.title()}" for topic in topics]) if topics else "### Topics\n- General"

    style_section = """### Style Patterns
- Extracted from post analysis above
- Review examples below for authentic voice"""

    examples_section = "## Example Posts\n\n" + "\n\n".join([f"```\n{ex}\n```" for ex in examples]) if examples else "## Example Posts\n\n(No examples extracted)"

    # Replace sections in the file
    # Find and replace the Voice Characteristics section
    voice_pattern = r"## Voice Characteristics.*?(?=---|\Z)"
    new_voice_section = f"""## Voice Characteristics

> Extracted from @KRAM_btc post analysis on {datetime.now().strftime('%Y-%m-%d')}

{tone_section}

{phrases_section}

{topics_section}

{style_section}

---

"""
    content = re.sub(voice_pattern, new_voice_section, content, flags=re.DOTALL)

    # Replace examples section
    examples_pattern = r"## Example Posts.*?(?=---|\Z)"
    new_examples_section = f"""{examples_section}

---

"""
    content = re.sub(examples_pattern, new_examples_section, content, flags=re.DOTALL)

    # Write updated file
    with open(VOICE_PROFILE_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Updated voice profile at {VOICE_PROFILE_PATH}")


def main():
    print("=" * 50)
    print("Voice Analysis for @KRAM_btc")
    print("=" * 50)

    # Step 1: Scrape posts
    posts = scrape_user_posts(USERNAME, MAX_POSTS)

    if not posts:
        print("\nNo posts available for analysis.")
        print("\nOptions:")
        print("1. Add APIFY_API_KEY to .env (sign up free at apify.com)")
        print("2. Manually add posts to .tmp/sample_posts.json")
        return

    # Step 2: Extract text content
    texts = extract_text_content(posts)
    print(f"\nExtracted {len(texts)} text posts for analysis")

    if not texts:
        print("No text content found in posts")
        return

    # Step 3: Analyze tone
    print("\nAnalyzing tone patterns...")
    tone_analysis = analyze_tone(texts)
    for key, value in tone_analysis.items():
        print(f"  {key}: {value}")

    # Step 4: Extract common phrases
    print("\nExtracting common phrases...")
    phrases = extract_common_phrases(texts)
    for phrase in phrases[:5]:
        print(f"  - \"{phrase}\"")

    # Step 5: Extract topics
    print("\nIdentifying topics...")
    topics = extract_topics(texts)
    print(f"  Topics: {', '.join(topics) if topics else 'None detected'}")

    # Step 6: Select example posts
    print("\nSelecting best example posts...")
    examples = select_example_posts(posts, count=5)

    # Step 7: Update voice profile
    print("\nUpdating voice profile...")
    update_voice_profile(tone_analysis, phrases, topics, examples)

    print("\n" + "=" * 50)
    print("Voice analysis complete!")
    print(f"Review: {VOICE_PROFILE_PATH}")
    print("=" * 50)


if __name__ == "__main__":
    main()
