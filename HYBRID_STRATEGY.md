# Hybrid Fetch Strategy

## AI-Friendly Sources → Option A (Full Automation)

| Source | Why AI-Friendly | Implementation |
|--------|-----------------|----------------|
| **V2EX RSS** | Open RSS feed, no auth, clean HTML | ✅ Automated fetch + score + notify |
| **GitHub Jobs** | API available, structured data | 🔄 Add to fetch skill |
| **LinkedIn RSS** | Standard RSS format | 🔄 Add to fetch skill |
| **RemoteOK/We Work Remotely** | Public APIs, tech-focused | 🔄 Future addition |

## Non-AI-Friendly Sources → Option B (Human-in-the-Loop)

| Source | Why Not AI-Friendly | Implementation |
|--------|---------------------|----------------|
| **BOSS直聘** | Anti-bot, no API, enterprise-only | 📋 Manual URL input → Agent analyzes |
| **猎聘** | No personal API, scraping fragile | 📋 Manual URL input → Agent analyzes |
| **拉勾网** | Font obfuscation, anti-scraping | 📋 Manual URL input → Agent analyzes |
| **智联招聘** | Requires real-name auth + face ID | 📋 Manual URL input → Agent analyzes (until API approved) |
| **微信公众号** | Hidden behind login, scattered | 📋 Manual paste → Agent extracts & analyzes |

## User Workflow

### For AI-Friendly Sources (Automated)
```
8:00 AM — Agent fetches from V2EX/GitHub/LinkedIn
8:05 AM — Agent scores opportunities
8:30 AM — Daily digest sent via iMessage
         ↓
You reply "apply 1" → Agent drafts email
You reply "save 2" → Added to tracker + calendar
You reply "skip" → Marked rejected, learns preference
```

### For Non-AI-Friendly Sources (Manual Bridge)
```
You browse BOSS/猎聘/智联 on your phone
Find interesting job → Copy URL
Paste to Agent (iMessage/Telegram)
         ↓
Agent fetches job details (if possible)
Agent scores match against your profile
Agent suggests application angle
Agent can draft cover letter
Agent adds to tracker
```

## Technical Implementation

### Phase 3A: Score Skill (Universal)
Works for ALL sources:
- Input: Job description + metadata
- Output: Match score + analysis + suggestions
- Feedback loop: 👍/👎 improves future scoring

### Phase 3B: Manual URL Analyzer
Special handler for Chinese platforms:
- Parse pasted URLs
- Extract job content (Playwright if needed)
- Run through same scoring pipeline
- Return formatted analysis

## Benefits of This Hybrid Approach

1. **Immediate Value** — Start using today with V2EX
2. **No Waiting** — Don't block on API approvals
3. **Best of Both** — Automation where possible, human judgment where needed
4. **Future-Proof** — Easy to add new sources as they become AI-friendly
5. **Respectful** — Doesn't violate platform ToS or fight anti-bot systems
