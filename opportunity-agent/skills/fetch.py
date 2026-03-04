"""
Fetch Skill - Pull opportunities from APIs + RSS + web search
"""
import json
import sqlite3
import feedparser
import requests
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class Opportunity:
    id: str
    source: str  # 'liepin', 'zhaopin', 'v2ex', etc.
    title: str
    company: str
    location: str
    description: str
    url: str
    salary: str = ""
    posted_date: str = ""
    raw_data: Dict = None
    fetched_at: str = None
    
    def __post_init__(self):
        if self.fetched_at is None:
            self.fetched_at = datetime.now().isoformat()
        if self.raw_data is None:
            self.raw_data = {}


class OpportunityFetcher:
    """Fetches opportunities from multiple sources."""
    
    def __init__(self, config: dict = None):
        if config is None:
            with open("config.json", 'r') as f:
                config = json.load(f)
        self.config = config
        self.sources = config.get('platforms', config.get('sources', {}))
        
    def fetch_all(self) -> List[Opportunity]:
        """Fetch from all configured sources."""
        all_ops = []
        
        # P0: Official APIs
        if self.sources.get('liepin', {}).get('enabled'):
            try:
                ops = self._fetch_liepin()
                all_ops.extend(ops)
                print(f"[fetch] Liepin: {len(ops)} opportunities")
            except Exception as e:
                print(f"[fetch] Liepin error: {e}")
                
        if self.sources.get('zhaopin', {}).get('enabled'):
            try:
                ops = self._fetch_zhaopin()
                all_ops.extend(ops)
                print(f"[fetch] Zhaopin: {len(ops)} opportunities")
            except Exception as e:
                print(f"[fetch] Zhaopin error: {e}")
        
        # P1: RSS feeds
        if self.sources.get('v2ex', {}).get('enabled'):
            try:
                ops = self._fetch_v2ex()
                all_ops.extend(ops)
                print(f"[fetch] V2EX: {len(ops)} opportunities")
            except Exception as e:
                print(f"[fetch] V2EX error: {e}")
        
        # P2: Web search (Sogou for WeChat articles)
        if self.sources.get('wechat_search', {}).get('enabled'):
            try:
                ops = self._fetch_wechat_search()
                all_ops.extend(ops)
                print(f"[fetch] WeChat Search: {len(ops)} opportunities")
            except Exception as e:
                print(f"[fetch] WeChat Search error: {e}")
        
        return all_ops
    
    def _fetch_liepin(self) -> List[Opportunity]:
        """Fetch from 猎聘 API (placeholder - needs real API credentials)."""
        # TODO: Implement actual Liepin API integration
        # API docs: https://www.liepin.com/api/
        # Requires: app_key, app_secret, access_token
        cfg = self.sources['liepin']
        print(f"[fetch] Liepin API not yet implemented (needs credentials)")
        return []
    
    def _fetch_zhaopin(self) -> List[Opportunity]:
        """Fetch from 智联 API (placeholder - needs real API credentials)."""
        # TODO: Implement actual Zhaopin API integration
        # Requires: real-name auth + face ID verification
        cfg = self.sources['zhaopin']
        print(f"[fetch] Zhaopin API not yet implemented (needs credentials)")
        return []
    
    def _fetch_v2ex(self) -> List[Opportunity]:
        """Fetch from V2EX jobs RSS feed."""
        rss_url = self.sources['v2ex'].get('rss_url', 'https://www.v2ex.com/feed/jobs.xml')
        
        feed = feedparser.parse(rss_url)
        opportunities = []
        
        for entry in feed.entries[:20]:  # Limit to recent 20
            op = Opportunity(
                id=f"v2ex_{entry.get('id', '')}",
                source='v2ex',
                title=entry.get('title', ''),
                company=self._extract_company_from_v2ex(entry),
                location='Remote/Various',  # V2EX often doesn't specify
                description=entry.get('summary', entry.get('description', ''))[:2000],
                url=entry.get('link', ''),
                posted_date=entry.get('published', ''),
                raw_data=dict(entry)
            )
            opportunities.append(op)
        
        return opportunities
    
    def _extract_company_from_v2ex(self, entry) -> str:
        """Extract company name from V2EX entry title."""
        title = entry.get('title', '')
        # Common patterns: "[Company] Role" or "Company - Role"
        if '[' in title and ']' in title:
            return title.split(']')[0].replace('[', '').strip()
        if ' - ' in title:
            return title.split(' - ')[0].strip()
        return "Unknown"
    
    def _fetch_wechat_search(self) -> List[Opportunity]:
        """Search WeChat articles via Sogou (placeholder)."""
        # TODO: Implement Sogou WeChat search scraping
        # URL: https://weixin.sogou.com/
        # Challenge: Anti-bot protection, requires careful handling
        print(f"[fetch] WeChat Search not yet implemented")
        return []
    
    def save_to_db(self, opportunities: List[Opportunity], db_path: str):
        """Save fetched opportunities to SQLite database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        inserted = 0
        skipped = 0
        
        for op in opportunities:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO opportunities 
                    (id, source, title, company, location, description, url, salary, 
                     posted_date, fetched_at, score, status, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 'new', ?)
                ''', (
                    op.id, op.source, op.title, op.company, op.location,
                    op.description, op.url, op.salary, op.posted_date,
                    op.fetched_at, json.dumps(op.raw_data)
                ))
                if cursor.rowcount > 0:
                    inserted += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"[fetch] DB error for {op.id}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"[fetch] Saved: {inserted} new, {skipped} duplicates skipped")
        return inserted


if __name__ == "__main__":
    # Test the fetch skill
    fetcher = FetchSkill()
    ops = fetcher.fetch_all()
    print(f"\nTotal fetched: {len(ops)}")
    for op in ops[:3]:
        print(f"- [{op.source}] {op.title} @ {op.company}")
