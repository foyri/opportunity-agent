#!/usr/bin/env python3
"""
Opportunity Matching Agent - Main Entry Point
Orchestrates fetch → score → act workflow
"""

import argparse
import json
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add skills directory to path
sys.path.insert(0, str(Path(__file__).parent / "skills"))

from skills.fetch import FetchSkill
from skills.score import ScoreSkill
from skills.act import ActSkill


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / "data" / "agent.log"),
    ],
)
logger = logging.getLogger("opportunity-agent")


def load_config(config_path: Path) -> dict:
    """Load and validate configuration file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # Validate required fields
    required_fields = ["user_profile", "apis", "preferences"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required config field: {field}")
    
    return config


def init_database(db_path: Path) -> sqlite3.Connection:
    """Initialize SQLite database with required tables."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()
    
    # Opportunities table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            external_id TEXT UNIQUE,
            title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            description TEXT,
            url TEXT,
            salary_min INTEGER,
            salary_max INTEGER,
            posted_date TEXT,
            deadline TEXT,
            raw_data TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'new'
        )
    """)
    
    # Scores table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            confidence TEXT,
            fits TEXT,
            gaps TEXT,
            angle TEXT,
            scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
        )
    """)
    
    # Actions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
        )
    """)
    
    # Feedback table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            opportunity_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
        )
    """)
    
    conn.commit()
    logger.info(f"Database initialized at {db_path}")
    return conn


def run_agent(config: dict, conn: sqlite3.Connection, test_mode: bool = False) -> None:
    """Run the full agent workflow: fetch → score → act."""
    logger.info("Starting opportunity agent workflow")
    
    # Initialize skills
    fetch_skill = FetchSkill(config["apis"], conn)
    score_skill = ScoreSkill(config["user_profile"], conn)
    act_skill = ActSkill(config["preferences"], conn)
    
    # Step 1: Fetch opportunities
    logger.info("Step 1: Fetching opportunities...")
    new_opportunities = fetch_skill.run(test_mode=test_mode)
    logger.info(f"Fetched {len(new_opportunities)} new opportunities")
    
    if test_mode:
        logger.info("Test mode: skipping scoring and actions")
        return
    
    # Step 2: Score opportunities
    logger.info("Step 2: Scoring opportunities...")
    high_matches = score_skill.run(new_opportunities)
    logger.info(f"Found {len(high_matches)} high matches (score >= 80)")
    
    # Step 3: Act on high matches
    logger.info("Step 3: Acting on high matches...")
    actions_taken = act_skill.run(high_matches)
    logger.info(f"Took {len(actions_taken)} actions")
    
    logger.info("Agent workflow completed successfully")


def test_mode(config: dict, conn: sqlite3.Connection) -> bool:
    """Run in test mode to verify setup."""
    try:
        logger.info("Running in TEST MODE")
        
        # Test config validation
        logger.info("✓ Config loaded and validated")
        
        # Test database connection
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        logger.info("✓ Database connection working")
        
        # Test skill imports
        fetch_skill = FetchSkill(config["apis"], conn)
        score_skill = ScoreSkill(config["user_profile"], conn)
        act_skill = ActSkill(config["preferences"], conn)
        logger.info("✓ All skills imported successfully")
        
        # Run stubbed workflow
        run_agent(config, conn, test_mode=True)
        
        logger.info("✓ TEST MODE PASSED - All systems operational")
        return True
        
    except Exception as e:
        logger.error(f"✗ TEST MODE FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Opportunity Matching Agent - Daily job opportunity scanner"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode to verify setup",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent / "config.json",
        help="Path to config file",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path(__file__).parent / "data" / "opportunities.db",
        help="Path to SQLite database",
    )
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Initialize database
        conn = init_database(args.db)
        
        if args.test:
            success = test_mode(config, conn)
            sys.exit(0 if success else 1)
        else:
            run_agent(config, conn)
            
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    main()
