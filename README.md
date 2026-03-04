# Opportunity Matching Agent

Autonomous AI agent that daily scans for job opportunities, intelligently matches them to Laurence's profile, and manages the application workflow with calendar integration.

---

## Quick Links

| File | Purpose |
|------|---------|
| [GOAL.md](GOAL.md) | Vision & success criteria |
| [PLAN.md](PLAN.md) | Current execution plan (lean v2026-03-03) |
| [RESEARCH.md](RESEARCH.md) | Platform analysis & API matrix |
| [LOG.md](LOG.md) | Development journal |

---

## Status

🟡 **Planning** — Awaiting approval to spawn Coding Agent

---

## Core Architecture

```
┌─────────┐    ┌─────────┐    ┌─────────┐
│  FETCH  │ →  │  SCORE  │ →  │   ACT   │
│ (daily) │    │(LLM judge)│   │(as needed)│
└─────────┘    └─────────┘    └─────────┘
     ↑                              ↓
     └────── Feedback loop ←───────┘
```

3 skills. ~2 weeks. No bloat.
