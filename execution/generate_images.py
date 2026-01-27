"""
Image Generator using OpenAI DALL-E 3
Generates contextual images for each draft post featuring MAYC #11555.

Usage: python execution/generate_images.py [--date YYYY-MM-DD]

Requires: OPENAI_API_KEY in .env
"""

import os
import sys
import json
import time
import re
import requests
import base64
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    print("Please install openai: pip install openai")
    sys.exit(1)

# Load environment variables
load_dotenv(override=True)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
IMAGES_DIR = DASHBOARD_DIR / "images"

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = "dall-e-3"
IMAGE_SIZE = "1024x1024"
IMAGE_QUALITY = "standard"  # "standard" or "hd"

# Rate limiting
DELAY_BETWEEN_CALLS = 3  # seconds

# MAYC #11555 Character Description for consistent image generation
MAYC_CHARACTER = """A stylized cartoon mutant ape character with:
- Leopard/cheetah spotted tan and gold fur pattern
- Glowing gold cyber eyes with dripping golden serum
- Bright radioactive green teeth in a wide grin
- White bunny ears with pink interior (mutation)
- Brown scruffy beard
- Small leopard cub companion on shoulder
- Purple and blue background tones
The character has a fun, slightly unhinged but friendly energy."""


def analyze_post_theme(draft_text: str) -> dict:
    """Analyze the draft text to determine image theme and elements."""
    text_lower = draft_text.lower()

    theme = {
        "type": "general",
        "mood": "energetic",
        "time_of_day": None,
        "elements": [],
        "colors": ["purple", "blue", "gold"],
        "setting": "abstract crypto/web3 background"
    }

    # GM (Good Morning) posts
    if any(word in text_lower for word in ["gm", "good morning", "morning", "wake up", "rise"]):
        theme["type"] = "morning"
        theme["mood"] = "cheerful"
        theme["time_of_day"] = "sunrise"
        theme["elements"] = ["coffee cup", "sunrise", "warm orange glow", "steam rising"]
        theme["colors"] = ["orange", "gold", "pink", "warm tones"]
        theme["setting"] = "cozy morning scene with sunrise through window"

    # GN (Good Night) posts
    elif any(word in text_lower for word in ["gn", "good night", "night", "sleep", "rest"]):
        theme["type"] = "night"
        theme["mood"] = "peaceful"
        theme["time_of_day"] = "night"
        theme["elements"] = ["moon", "stars", "cozy blanket", "night sky"]
        theme["colors"] = ["deep blue", "purple", "silver", "soft glow"]
        theme["setting"] = "peaceful night scene with starry sky"

    # Bitcoin/Mining posts
    elif any(word in text_lower for word in ["bitcoin", "btc", "mining", "bitaxe", "sats", "hash", "miner"]):
        theme["type"] = "bitcoin"
        theme["mood"] = "tech-focused"
        theme["elements"] = ["bitcoin symbols", "mining equipment", "orange glow", "circuit patterns"]
        theme["colors"] = ["orange", "gold", "black", "electric blue"]
        theme["setting"] = "futuristic mining setup with glowing screens"

    # Otherside/Metaverse posts
    elif any(word in text_lower for word in ["otherside", "metaverse", "virtual", "avatar", "nexus"]):
        theme["type"] = "metaverse"
        theme["mood"] = "futuristic"
        theme["elements"] = ["portal", "digital landscape", "floating islands", "neon lights"]
        theme["colors"] = ["neon purple", "cyan", "pink", "electric blue"]
        theme["setting"] = "surreal metaverse landscape with floating elements"

    # NFT/Community posts
    elif any(word in text_lower for word in ["nft", "mayc", "bayc", "ape", "community", "fam", "web3"]):
        theme["type"] = "community"
        theme["mood"] = "social"
        theme["elements"] = ["group gathering", "digital art frames", "community vibes"]
        theme["colors"] = ["purple", "blue", "gold", "green"]
        theme["setting"] = "vibrant web3 community space"

    # Weekend/Chill posts
    elif any(word in text_lower for word in ["weekend", "saturday", "sunday", "chill", "relax", "vibes"]):
        theme["type"] = "weekend"
        theme["mood"] = "relaxed"
        theme["elements"] = ["lounging", "tropical elements", "sunglasses", "beach vibes"]
        theme["colors"] = ["teal", "coral", "sunset orange", "palm green"]
        theme["setting"] = "tropical relaxation scene"

    # Hype/Excitement posts
    elif any(word in text_lower for word in ["let's go", "lfg", "huge", "bullish", "pump", "moon", "wagmi"]):
        theme["type"] = "hype"
        theme["mood"] = "excited"
        theme["elements"] = ["rocket", "explosion effects", "energy burst", "confetti"]
        theme["colors"] = ["bright green", "gold", "electric purple", "white flash"]
        theme["setting"] = "explosive celebration with energy effects"

    return theme


def build_image_prompt(theme: dict) -> str:
    """Build DALL-E prompt based on theme analysis."""

    base_prompt = f"""Digital art illustration of {MAYC_CHARACTER}

Scene: {theme['setting']}
Mood: {theme['mood']}
Key elements: {', '.join(theme['elements']) if theme['elements'] else 'abstract web3 elements'}
Color palette: {', '.join(theme['colors'])}

Style: Modern digital art, vibrant colors, clean lines, slightly cartoonish but detailed.
The image should feel fun, crypto-native, and social media ready.
Square format, centered composition with the ape character as the main focus.
No text or words in the image."""

    # Add time-specific details
    if theme["time_of_day"] == "sunrise":
        base_prompt += "\nLighting: Warm golden hour light, soft morning glow."
    elif theme["time_of_day"] == "night":
        base_prompt += "\nLighting: Soft moonlight, twinkling stars, cozy ambient glow."

    return base_prompt


def generate_image(client: OpenAI, prompt: str, draft_id: str) -> str | None:
    """Generate an image using DALL-E 3 and save it."""
    try:
        response = client.images.generate(
            model=MODEL,
            prompt=prompt,
            size=IMAGE_SIZE,
            quality=IMAGE_QUALITY,
            n=1,
            response_format="url"
        )

        image_url = response.data[0].url
        revised_prompt = response.data[0].revised_prompt

        print(f"    DALL-E revised prompt: {revised_prompt[:100]}...")

        # Download and save image
        img_response = requests.get(image_url, timeout=30)
        if img_response.status_code == 200:
            IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            image_filename = f"{draft_id}.png"
            image_path = IMAGES_DIR / image_filename

            with open(image_path, "wb") as f:
                f.write(img_response.content)

            print(f"    Saved image: {image_path}")
            return f"images/{image_filename}"
        else:
            print(f"    Failed to download image: {img_response.status_code}")
            return None

    except Exception as e:
        print(f"    Error generating image: {e}")
        return None


def process_drafts(date_str: str | None = None):
    """Process drafts and generate images for each."""

    # Load drafts from dashboard
    drafts_file = DASHBOARD_DIR / "drafts.json"

    if not drafts_file.exists():
        print("No drafts.json found")
        return

    with open(drafts_file, "r", encoding="utf-8") as f:
        drafts = json.load(f)

    # Filter drafts that need images
    drafts_needing_images = [
        d for d in drafts
        if not d.get("image_path") and d.get("status") == "pending"
    ]

    if date_str:
        # Only process drafts from specific date
        drafts_needing_images = [
            d for d in drafts_needing_images
            if d.get("created_at", "").startswith(date_str)
        ]

    print(f"Found {len(drafts_needing_images)} drafts needing images")

    if not drafts_needing_images:
        print("No drafts need image generation")
        return

    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Generate images
    for i, draft in enumerate(drafts_needing_images, 1):
        draft_id = draft.get("id", "unknown")
        draft_text = draft.get("draft", "")

        print(f"\n[{i}/{len(drafts_needing_images)}] Processing draft: {draft_id[:8]}...")
        print(f"    Text: {draft_text[:60]}...")

        # Analyze theme
        theme = analyze_post_theme(draft_text)
        print(f"    Theme: {theme['type']} / {theme['mood']}")

        # Build prompt
        prompt = build_image_prompt(theme)

        # Generate image
        image_path = generate_image(client, prompt, draft_id)

        if image_path:
            # Update draft with image path
            for d in drafts:
                if d.get("id") == draft_id:
                    d["image_path"] = image_path
                    d["image_theme"] = theme["type"]
                    break

        # Rate limiting
        if i < len(drafts_needing_images):
            time.sleep(DELAY_BETWEEN_CALLS)

    # Save updated drafts
    with open(drafts_file, "w", encoding="utf-8") as f:
        json.dump(drafts, f, indent=2, ensure_ascii=False)

    print(f"\nUpdated {drafts_file}")


def main():
    print("=" * 50)
    print("DALL-E 3 Image Generator")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # Check API key
    if not OPENAI_API_KEY:
        print("\nERROR: OPENAI_API_KEY not found in .env")
        print("Get your API key from: https://platform.openai.com/api-keys")
        print("Add OPENAI_API_KEY=your_key to .env")
        sys.exit(1)

    # Parse date argument
    date_str = None
    if len(sys.argv) > 1 and sys.argv[1] == "--date" and len(sys.argv) > 2:
        date_str = sys.argv[2]
        print(f"Processing date: {date_str}")

    # Process drafts
    process_drafts(date_str)

    print("\n" + "=" * 50)
    print("Image generation complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
