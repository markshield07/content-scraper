# MAYC #11555 Content Pipeline

Automated content generation for @KRAM_btc based on posts from followed accounts.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up API Keys

Copy `.env.example` to `.env` and add your keys:

```bash
# Required
APIFY_API_KEY=your_apify_token      # Free at https://apify.com
ANTHROPIC_API_KEY=your_claude_key   # From https://console.anthropic.com
```

### 3. Analyze Your Voice (One-Time)

```bash
python execution/analyze_voice.py
```

This scrapes your @KRAM_btc posts and builds a voice profile.

### 4. Run the Pipeline

```bash
python main.py
```

Or run steps individually:
```bash
python execution/scrape_x.py       # Scrape target accounts
python execution/generate_posts.py  # Generate drafts
```

### 5. Review Drafts

Open `dashboard/index.html` in your browser to:
- View generated drafts
- Approve/reject content
- Copy to clipboard for posting

## Automated Daily Runs (GitHub Actions)

1. Push this repo to GitHub
2. Go to Settings → Secrets → Actions
3. Add secrets:
   - `APIFY_API_KEY`
   - `ANTHROPIC_API_KEY`
4. Enable GitHub Pages (Settings → Pages → Source: main branch, /dashboard folder)
5. The pipeline runs daily at 6am PST

## Project Structure

```
├── main.py                 # Main orchestration script
├── execution/
│   ├── analyze_voice.py    # Build voice profile from your posts
│   ├── scrape_x.py         # Scrape target X accounts
│   └── generate_posts.py   # Generate content with Claude
├── directives/
│   ├── voice_profile.md    # Your digital identity
│   ├── scrape_x_accounts.md
│   └── generate_content.md
├── dashboard/
│   ├── index.html          # Approval UI
│   ├── style.css
│   ├── app.js
│   └── drafts.json         # Current drafts
├── drafts/                 # Historical drafts by date
├── .tmp/                   # Temporary files (scraped data)
└── .github/workflows/      # GitHub Actions automation
```

## Target Accounts

Currently following:
- @TheCaliApe
- @tboe3D
- @Gratefulape
- @MookieNFT

Edit `execution/scrape_x.py` to change accounts.

## Costs

- **Apify**: ~$2/month (free tier available)
- **Claude API**: ~$0.50/month at current usage

## Troubleshooting

**"APIFY_API_KEY not found"**
- Create `.env` file with your API key
- Sign up free at https://apify.com

**"No posts scraped"**
- Check if target accounts have posted in last 12 hours
- Verify Apify API key is valid

**"Voice profile not populated"**
- Run `python execution/analyze_voice.py` first
- Or manually add example posts to voice_profile.md
