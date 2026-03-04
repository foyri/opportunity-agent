# Opportunity Matching Agent

Autonomous AI agent that daily scans for job opportunities, intelligently matches them to Laurence's profile, and manages the application workflow with calendar integration.

## Quick Start

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run once (dry run - fetches and scores but doesn't send notifications)
python3 run.py --dry-run

# Run full pipeline
python3 run.py
```

## Architecture

```
┌─────────┐    ┌─────────┐    ┌─────────┐
│  FETCH  │ →  │  SCORE  │ →  │   ACT   │
│ (daily) │    │(LLM judge)│   │(as needed)│
└─────────┘    └─────────┘    └─────────┘
     ↑                              ↓
     └────── Feedback loop ←───────┘
```

### Skills

- **fetch.py** - Pulls from APIs + RSS feeds (V2EX working, 猎聘/智联 need API keys)
- **score.py** - LLM-based match analysis with structured output
- **act.py** - Notifications, calendar integration, email drafting

## Configuration

Edit `config.json`:

```json
{
  "profile": { /* Your profile */ },
  "preferences": { /* Scoring thresholds, roles, locations */ },
  "platforms": {
    "v2ex": { "enabled": true },  // Working now
    "liepin": { "enabled": false, "api_key": "" },  // Needs API key
    "zhaopin": { "enabled": false, "api_key": "" }  // Needs API key
  }
}
```

## Cron Setup

Add to crontab for daily 8 AM runs:

```bash
0 8 * * * cd /Users/laurence/.openclaw/workspace-pm/Projects/opportunity-matching/opportunity-agent && /usr/bin/python3 run.py >> logs/cron.log 2>&1
```

Or use OpenClaw's built-in cron:

```bash
openclaw cron add --name opportunity-agent --schedule "0 8 * * *" \
  --command "cd /Users/laurence/.openclaw/workspace-pm/Projects/opportunity-matching/opportunity-agent && python3 run.py"
```

## Data Flow

1. **Fetch** - Pulls opportunities from enabled platforms
2. **Deduplicate** - Skips already-seen opportunities (by ID)
3. **Score** - LLM analyzes fit against your profile (0-100)
4. **Notify** - Sends digest via configured channel (Telegram/iMessage)
5. **Track** - Saves to SQLite for history and feedback loop

## Database Schema

```sql
CREATE TABLE opportunities (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,      -- 'v2ex', 'liepin', 'zhaopin'
    platform TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    description TEXT,
    url TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    posted_date TEXT,
    fetched_at TEXT,
    score INTEGER,             -- 0-100 match score
    confidence TEXT,           -- 'high', 'medium', 'low'
    fits TEXT,                 -- JSON array of why it's a good fit
    gaps TEXT,                 -- JSON array of concerns
    angle TEXT,                -- Strategic positioning advice
    status TEXT DEFAULT 'new'  -- 'new', 'saved', 'applied', 'rejected'
);
```

## Next Steps

### Phase 2: Fetch (In Progress)
- [ ] Add 猎聘 API integration (needs credentials)
- [ ] Add 智联 API integration (needs credentials)
- [x] V2EX RSS working ✓

### Phase 3: Score
- [ ] Replace mock LLM with actual API call (OpenAI/Claude)
- [ ] Implement feedback learning loop

### Phase 4: Act
- [ ] iMessage notifications via AppleScript
- [ ] Calendar integration for deadlines
- [ ] Email draft generation

## Platform Status

| Platform | Status | Notes |
|----------|--------|-------|
| V2EX | ✅ Working | RSS feed active |
| 猎聘 | ⏳ Pending | Needs API credentials |
| 智联 | ⏳ Pending | Needs real-name auth |
| BOSS直聘 | 🚫 Skipped | Anti-bot too aggressive |
| 拉勾网 | 🚫 Skipped | Enterprise only |
