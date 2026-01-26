# Directive: Generate Content

## Purpose
Transform scraped posts from target accounts into original content in @KRAM_btc's voice (Mutant Ape #11555).

## Inputs
- Scraped posts: `.tmp/scraped_{date}.json`
- Voice profile: `directives/voice_profile.md`

## Execution
```bash
python execution/generate_posts.py
```

## Output
- File: `drafts/pending_{date}.json`
- Dashboard update: `dashboard/drafts.json`

### Draft Object Schema
```json
{
  "id": "uuid",
  "created_at": "ISO timestamp",
  "source": {
    "username": "original_account",
    "text": "original_post",
    "url": "link_to_original"
  },
  "draft": "generated_post_text",
  "status": "pending",
  "notes": ""
}
```

## Generation Process

### 1. Load Voice Profile
- Read `directives/voice_profile.md`
- Extract tone, phrases, topics, examples
- Build system prompt

### 2. Filter Source Posts
- Skip posts that are:
  - Pure retweets
  - Too short (< 20 chars)
  - Just links with no commentary
  - Off-topic (not relevant to NFT/crypto/community)

### 3. Generate Drafts
For each qualifying source post:
- Send to Claude API with voice profile context
- Request 1 draft that:
  - Takes the core insight/topic
  - Rewrites in @KRAM_btc's voice
  - Is original, not a copy
  - Maintains appropriate length for X

### 4. Quality Filter
- Discard drafts that are:
  - Too similar to source (> 50% word overlap)
  - Generic/bland
  - Off-brand

## Claude API Configuration
- Model: claude-sonnet-4-20250514 (fast, cost-effective)
- Max tokens: 300
- Temperature: 0.8 (creative but not wild)

## Rate Limiting
- Max 10 API calls per run
- 1 second delay between calls
- Total cost per run: ~$0.02

## Edge Cases

### Empty scraped posts
- Log message, create empty drafts file
- Don't call API

### API failure
- Log error
- Retry once after 5 seconds
- If still fails, skip that post

### Voice profile not populated
- Warn user to run `analyze_voice.py` first
- Use fallback generic prompt

## Success Criteria
- At least 1 draft generated (if posts available)
- Output file created and valid JSON
- Dashboard updated

## Learnings
*(To be updated as we learn from runs)*

---

*Last updated: 2026-01-26*
