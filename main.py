"""
Main Orchestration Script
Runs the full content pipeline: scrape → generate → update dashboard

Usage: python main.py

This is the entry point for both local runs and GitHub Actions.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


def run_script(script_name: str) -> bool:
    """Run a Python script and return success status."""
    script_path = PROJECT_ROOT / "execution" / script_name

    print(f"\n{'='*50}")
    print(f"Running: {script_name}")
    print('='*50)

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=False,  # Show output in real-time
        )
        return result.returncode == 0
    except Exception as e:
        print(f"ERROR: Failed to run {script_name}: {e}")
        return False


def main():
    print("=" * 60)
    print("MAYC #11555 Content Pipeline")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1: Scrape X accounts
    print("\n📡 Step 1: Scraping X accounts...")
    if not run_script("scrape_x.py"):
        print("WARNING: Scraping failed or returned no results")
        # Continue anyway - there might be cached data

    # Step 2: Generate content
    print("\n✍️ Step 2: Generating content drafts...")
    if not run_script("generate_posts.py"):
        print("ERROR: Content generation failed")
        sys.exit(1)

    # Summary
    print("\n" + "=" * 60)
    print("Pipeline Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Open dashboard/index.html in your browser")
    print("2. Review and approve/reject drafts")
    print("3. Copy approved drafts to post on X")
    print("\nOr view online at your GitHub Pages URL after pushing.")


if __name__ == "__main__":
    main()
