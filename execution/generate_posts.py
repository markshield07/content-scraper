"""
Content Generator
Takes scraped posts and generates drafts in @KRAM_btc's voice.

Usage: python execution/generate_posts.py [--date YYYY-MM-DD]

Output:
- drafts/pending_{date}.json
- dashboard/drafts.json (updated)

Requires: ANTHROPIC_API_KEY in .env
"""

import os
import sys
import json
import uuid
import time
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

try:
    import anthropic
except ImportError:
    print("Please install anthropic: pip install anthropic")
    sys.exit(1)

# Load environment variables
load_dotenv(override=True)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
TMP_DIR = PROJECT_ROOT / ".tmp"
DRAFTS_DIR = PROJECT_ROOT / "drafts"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
VOICE_PROFILE_PATH = PROJECT_ROOT / "directives" / "voice_profile.md"

# API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 300
TEMPERATURE = 0.8

# Limits
MAX_POSTS_TO_PROCESS = 10
DELAY_BETWEEN_CALLS = 1  # seconds


def load_voice_profile() -> dict:
    """Load and parse the voice profile."""
    if not VOICE_PROFILE_PATH.exists():
        print("WARNING: Voice profile not found")
        return {}

    with open(VOICE_PROFILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    profile = {
        "raw": content,
        "examples": [],
        "tone": "",
        "topics": [],
    }

    # Extract example posts
    example_pattern = r"```\n(.*?)\n```"
    examples = re.findall(example_pattern, content, re.DOTALL)
    profile["examples"] = [ex.strip() for ex in examples if len(ex.strip()) > 20]

    # Extract topics
    topics_match = re.search(r"### Topics\n(.*?)(?=###|---|\Z)", content, re.DOTALL)
    if topics_match:
        topics = re.findall(r"- (.*)", topics_match.group(1))
        profile["topics"] = [t.strip() for t in topics]

    # Extract tone info
    tone_match = re.search(r"### Tone\n(.*?)(?=###|---|\Z)", content, re.DOTALL)
    if tone_match:
        profile["tone"] = tone_match.group(1).strip()

    return profile


def build_system_prompt(profile: dict) -> str:
    """Build the system prompt for content generation."""

    examples_text = ""
    if profile.get("examples"):
        examples_text = "\n\nExample posts in your voice:\n" + "\n---\n".join(profile["examples"][:5])

    topics_text = ""
    if profile.get("topics"):
        topics_text = f"\n\nYour main topics: {', '.join(profile['topics'])}"

    tone_text = ""
    if profile.get("tone"):
        tone_text = f"\n\nYour tone patterns:\n{profile['tone']}"

    return f"""You are @KRAM_btc, the human behind Mutant Ape Yacht Club #11555.

Your visual identity: A leopard-furred mutant ape with gold dripping cyber eyes (with coin symbols), radioactive green teeth in a big grin, rare bunny ears mutation, brown beard, silver ear piercing, and a small leopard companion on your shoulder. Purple/blue background.

Your personality: You embrace the weird, don't take yourself too seriously, and are genuinely part of the NFT/crypto community. You're not a corporate shill - you're authentic, sometimes irreverent, and always real.
{tone_text}
{topics_text}
{examples_text}

Your task: Given a post from another creator, generate an ORIGINAL post in YOUR voice that:
1. Takes the core insight or interesting angle
2. Puts YOUR unique spin on it
3. Sounds authentically like you, not a copy
4. Is appropriate length for X (under 280 chars ideally)
5. Does NOT copy phrases directly from the source

Important: Be original. Don't just rephrase - add your own perspective. Your mutant ape energy should come through."""


def load_scraped_posts(date_str: str) -> list[dict]:
    """Load scraped posts for the given date."""
    scraped_file = TMP_DIR / f"scraped_{date_str}.json"

    if not scraped_file.exists():
        print(f"No scraped posts found for {date_str}")
        return []

    with open(scraped_file, "r", encoding="utf-8") as f:
        return json.load(f)


def filter_posts(posts: list[dict]) -> list[dict]:
    """Filter posts to only include ones worth generating from."""
    filtered = []

    for post in posts:
        text = post.get("text", "")

        # Skip very short posts
        if len(text) < 30:
            continue

        # Skip pure retweets
        if text.startswith("RT @"):
            continue

        # Skip posts that are mostly URLs
        text_without_urls = re.sub(r"https?://\S+", "", text).strip()
        if len(text_without_urls) < 20:
            continue

        filtered.append(post)

    return filtered


def generate_draft(client: anthropic.Anthropic, system_prompt: str, source_post: dict) -> str | None:
    """Generate a draft post from a source post."""
    source_text = source_post.get("text", "")
    source_username = source_post.get("username", "unknown")

    user_prompt = f"""Here's a post from @{source_username}:

"{source_text}"

Generate an original post in your voice (@KRAM_btc / Mutant Ape #11555) that takes inspiration from this but puts your own spin on it. Just output the post text, nothing else."""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        draft = response.content[0].text.strip()

        # Clean up any quotes or "Post:" prefix the model might add
        draft = re.sub(r'^["\']|["\']$', '', draft)
        draft = re.sub(r'^(Post|Tweet|Draft):\s*', '', draft, flags=re.IGNORECASE)

        return draft

    except anthropic.APIError as e:
        print(f"    API error: {e}")
        return None


def check_similarity(source: str, draft: str) -> float:
    """Check word overlap between source and draft (0-1)."""
    source_words = set(re.findall(r"\b\w+\b", source.lower()))
    draft_words = set(re.findall(r"\b\w+\b", draft.lower()))

    if not draft_words:
        return 0

    overlap = len(source_words & draft_words)
    return overlap / len(draft_words)


def save_drafts(drafts: list[dict], date_str: str):
    """Save drafts to file and update dashboard."""
    DRAFTS_DIR.mkdir(exist_ok=True)
    DASHBOARD_DIR.mkdir(exist_ok=True)

    # Save dated drafts file
    drafts_file = DRAFTS_DIR / f"pending_{date_str}.json"
    with open(drafts_file, "w", encoding="utf-8") as f:
        json.dump(drafts, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(drafts)} drafts to {drafts_file}")

    # Update dashboard drafts.json (merge with existing)
    dashboard_file = DASHBOARD_DIR / "drafts.json"
    existing_drafts = []

    if dashboard_file.exists():
        with open(dashboard_file, "r", encoding="utf-8") as f:
            try:
                existing_drafts = json.load(f)
            except json.JSONDecodeError:
                existing_drafts = []

    # Add new drafts (avoid duplicates by ID)
    existing_ids = {d.get("id") for d in existing_drafts}
    for draft in drafts:
        if draft.get("id") not in existing_ids:
            existing_drafts.append(draft)

    # Sort by created_at descending
    existing_drafts.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    # Keep only last 100 drafts
    existing_drafts = existing_drafts[:100]

    with open(dashboard_file, "w", encoding="utf-8") as f:
        json.dump(existing_drafts, f, indent=2, ensure_ascii=False)

    print(f"Updated dashboard: {dashboard_file}")


def main():
    print("=" * 50)
    print("Content Generator")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # Check API key
    if not ANTHROPIC_API_KEY:
        print("\nERROR: ANTHROPIC_API_KEY not found in .env")
        print("Sign up at https://console.anthropic.com")
        print("Add ANTHROPIC_API_KEY=your_key to .env")
        sys.exit(1)

    # Parse date argument
    date_str = datetime.now().strftime("%Y-%m-%d")
    if len(sys.argv) > 1 and sys.argv[1] == "--date" and len(sys.argv) > 2:
        date_str = sys.argv[2]

    print(f"\nProcessing date: {date_str}")

    # Load voice profile
    print("\nLoading voice profile...")
    profile = load_voice_profile()
    if not profile.get("examples"):
        print("WARNING: No example posts in voice profile.")
        print("Run 'python execution/analyze_voice.py' first for better results.")

    system_prompt = build_system_prompt(profile)

    # Load scraped posts
    print(f"\nLoading scraped posts...")
    posts = load_scraped_posts(date_str)
    print(f"Found {len(posts)} total posts")

    # Filter posts
    filtered_posts = filter_posts(posts)
    print(f"After filtering: {len(filtered_posts)} posts")

    if not filtered_posts:
        print("\nNo posts to process. Creating empty drafts file.")
        save_drafts([], date_str)
        return

    # Limit posts to process
    posts_to_process = filtered_posts[:MAX_POSTS_TO_PROCESS]
    print(f"Processing: {len(posts_to_process)} posts")

    # Initialize Anthropic client
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Generate drafts
    drafts = []
    print("\nGenerating drafts...")

    for i, post in enumerate(posts_to_process, 1):
        print(f"\n[{i}/{len(posts_to_process)}] @{post.get('username', 'unknown')}")
        print(f"  Source: {post.get('text', '')[:60].encode('ascii', 'replace').decode()}...")

        draft_text = generate_draft(client, system_prompt, post)

        if not draft_text:
            print("  SKIP: Generation failed")
            continue

        # Check similarity
        similarity = check_similarity(post.get("text", ""), draft_text)
        if similarity > 0.5:
            print(f"  SKIP: Too similar to source ({similarity:.0%} overlap)")
            continue

        # Create draft object
        draft = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "source": {
                "username": post.get("username", ""),
                "text": post.get("text", ""),
                "url": f"https://x.com/{post.get('username', '')}/status/{post.get('id', '')}",
            },
            "draft": draft_text,
            "status": "pending",
            "notes": "",
        }

        drafts.append(draft)
        print(f"  Draft: {draft_text[:60].encode('ascii', 'replace').decode()}...")

        # Rate limiting
        if i < len(posts_to_process):
            time.sleep(DELAY_BETWEEN_CALLS)

    # Save results
    save_drafts(drafts, date_str)

    # Summary
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    print(f"Posts processed: {len(posts_to_process)}")
    print(f"Drafts generated: {len(drafts)}")
    print(f"Success rate: {len(drafts)/len(posts_to_process)*100:.0f}%" if posts_to_process else "N/A")

    print("\n" + "=" * 50)
    print("Content generation complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
