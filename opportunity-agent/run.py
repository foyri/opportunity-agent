#!/usr/bin/env python3
"""
Opportunity Matching Agent - Main Entry Point
Daily cron @ 8AM: fetch → score → notify
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add skills to path
sys.path.insert(0, str(Path(__file__).parent / "skills"))

from fetch import OpportunityFetcher
from score import OpportunityScorer
from act import OpportunityActor


def init_database(db_path: Path):
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            platform TEXT NOT NULL,
            title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            description TEXT,
            url TEXT,
            salary_min INTEGER,
            salary_max INTEGER,
            posted_date TEXT,
            fetched_at TEXT DEFAULT CURRENT_TIMESTAMP,
            score INTEGER,
            confidence TEXT,
            fits TEXT,  -- JSON array
            gaps TEXT,  -- JSON array
            angle TEXT,
            status TEXT DEFAULT 'new',  -- new, saved, applied, rejected
            feedback TEXT  -- thumbs_up, thumbs_down
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_status ON opportunities(status);
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_score ON opportunities(score);
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {db_path}")


def load_config(config_path: Path) -> dict:
    """Load configuration from JSON file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """Main execution flow: fetch → score → notify."""
    # Setup paths
    base_dir = Path(__file__).parent
    config_path = base_dir / "config.json"
    db_path = base_dir / "data" / "opportunities.db"
    feedback_path = base_dir / "data" / "feedback.json"
    
    # Ensure data directory exists
    db_path.parent.mkdir(exist_ok=True)
    
    # Initialize database if needed
    if not db_path.exists():
        init_database(db_path)
    
    # Load configuration
    config = load_config(config_path)
    
    print(f"\n🎯 Opportunity Matching Agent")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👤 Profile: {config['profile']['name']}")
    print("=" * 50)
    
    # Phase 1: Fetch opportunities
    print("\n📡 Phase 1: Fetching opportunities...")
    fetcher = OpportunityFetcher(config)
    opportunities = fetcher.fetch_all()
    print(f"   Found {len(opportunities)} opportunities")
    
    if not opportunities:
        print("   No opportunities found today.")
        return
    
    # Phase 2: Score opportunities
    print("\n🧠 Phase 2: Scoring opportunities...")
    scorer = OpportunityScorer(config)
    scored_opportunities = scorer.score_batch(opportunities)
    
    # Count by category
    high_matches = [o for o in scored_opportunities if o.get('score', 0) >= 80]
    medium_matches = [o for o in scored_opportunities if 60 <= o.get('score', 0) < 80]
    
    print(f"   High matches (80+): {len(high_matches)}")
    print(f"   Medium matches (60-79): {len(medium_matches)}")
    
    # Phase 3: Act on opportunities
    print("\n🔔 Phase 3: Sending notifications...")
    actor = OpportunityActor(config)
    actor.notify(scored_opportunities)
    
    # Save to database
    print("\n💾 Saving to database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for opp in scored_opportunities:
        cursor.execute("""
            INSERT OR REPLACE INTO opportunities 
            (id, source, platform, title, company, location, description, url,
             salary_min, salary_max, posted_date, score, confidence, fits, gaps, angle)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            opp['id'],
            opp.get('source', 'unknown'),
            opp.get('platform', 'unknown'),
            opp.get('title', 'Unknown Title'),
            opp.get('company'),
            opp.get('location'),
            opp.get('description', ''),
            opp.get('url'),
            opp.get('salary_min'),
            opp.get('salary_max'),
            opp.get('posted_date'),
            opp.get('score'),
            opp.get('confidence'),
            json.dumps(opp.get('fits', []), ensure_ascii=False),
            json.dumps(opp.get('gaps', []), ensure_ascii=False),
            opp.get('angle')
        ))
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Done! Processed {len(scored_opportunities)} opportunities.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
