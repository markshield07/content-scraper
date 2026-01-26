# Directive: Scrape X Accounts

## Purpose
Scrape posts from target X accounts to gather content inspiration for generating posts in @KRAM_btc's voice.

## Schedule
- **Frequency**: Daily at 6am PST (14:00 UTC)
- **Time window**: Posts from last 12 hours

## Target Accounts
1. @TheCaliApe
2. @tboe3D
3. @Gratefulape
4. @MookieNFT

## Inputs
- List of usernames (configured in script)
- Time window (12 hours)
- APIFY_API_KEY from .env

## Execution
```bash
python execution/scrape_x.py
```

## Output
- File: `.tmp/scraped_{YYYY-MM-DD}.json`
- Format: JSON array of post objects

### Post Object Schema
```json
{
  "id": "tweet_id",
  "username": "account_handle",
  "text": "post content",
  "created_at": "ISO timestamp",
  "likes": 0,
  "retweets": 0,
  "replies": 0,
  "media_urls": []
}
```

## Edge Cases

### No posts in time window
- Log message, continue with empty results
- Don't fail the pipeline

### Account not found / private
- Log warning
- Skip to next account
- Continue pipeline

### Apify API failure
- Log error with details
- Retry once after 30 seconds
- If still fails, exit with error code

### Rate limiting
- Apify handles this internally
- If rate limited, wait and retry

## Success Criteria
- At least 1 post scraped from at least 1 account
- Output file created and valid JSON
- No unhandled exceptions

## Learnings
- snscrape incompatible with Python 3.13 (AttributeError on FileFinder)
- Nitter instances frequently go down
- Apify is most reliable (free tier: ~$5/month in credits)

---

*Last updated: 2026-01-26*
