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
import hashlib


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
        self.mock_mode = True  # Enable mock data for development

    def fetch_all(self) -> List[Opportunity]:
        """Fetch from all configured sources."""
        all_ops = []

        # P0: Official APIs (mock mode for now)
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

        return all_ops

    def _fetch_liepin(self) -> List[Opportunity]:
        """Fetch from 猎聘 (Liepin).
        
        NOTE: Liepin does NOT offer personal API access. Enterprise API costs 9800+ 元/年.
        Options:
        1. Mock mode (default) - for development/testing
        2. Web scraping - requires Playwright (may break due to anti-bot)
        3. Manual browsing - user searches manually, agent helps analyze
        """
        cfg = self.sources['liepin']

        if self.mock_mode:
            print("[fetch] Liepin: Using MOCK data (no personal API available)")
            return self._mock_liepin_data()

        # Future: Implement web scraping with Playwright
        # WARNING: Fragile, may require constant maintenance
        return self._scrape_liepin_web(cfg)

    def _mock_liepin_data(self) -> List[Opportunity]:
        """Generate realistic mock data for Liepin."""
        mock_jobs = [
            {
                "title": "AI产品经理",
                "company": "字节跳动",
                "location": "北京·海淀区",
                "salary": "40-70K·16薪",
                "description": "负责AI教育产品的规划与设计，推动AI技术在教育场景落地。要求：1年以上产品经验，熟悉AI技术，有教育行业背景优先。",
                "url": "https://www.liepin.com/job/1912867312.shtml"
            },
            {
                "title": "高级AI产品专家",
                "company": "阿里巴巴",
                "location": "杭州·余杭区",
                "salary": "50-80K·16薪",
                "description": "主导通义千问教育版产品战略，设计AI Tutor交互体验。需要强技术背景和产品sense，有LLM产品经验加分。",
                "url": "https://www.liepin.com/job/1912834567.shtml"
            },
            {
                "title": "AI教育产品负责人",
                "company": "好未来",
                "location": "北京·昌平区",
                "salary": "35-60K·14薪",
                "description": "负责学而思AI学习机产品线，结合大模型能力打造个性化学习体验。要求：3年+教育产品经验，对AI+教育有深入理解。",
                "url": "https://www.liepin.com/job/1912812345.shtml"
            },
            {
                "title": "AIGC产品经理",
                "company": "腾讯",
                "location": "深圳·南山区",
                "salary": "45-75K·18薪",
                "description": "负责腾讯智影、AI绘画等AIGC产品，探索生成式AI在内容创作领域的应用。需要有内容产品经验，对AIGC趋势敏感。",
                "url": "https://www.liepin.com/job/1912898765.shtml"
            },
            {
                "title": "AI创新业务产品经理",
                "company": "美团",
                "location": "北京·朝阳区",
                "salary": "40-65K·15薪",
                "description": "探索AI在本地生活服务中的应用，如智能客服、推荐系统优化等。要求快速学习能力，能接受从0到1的创新项目。",
                "url": "https://www.liepin.com/job/1912854321.shtml"
            }
        ]

        opportunities = []
        for i, job in enumerate(mock_jobs):
            op_id = f"liepin_mock_{hashlib.md5(job['url'].encode()).hexdigest()[:12]}"
            op = Opportunity(
                id=op_id,
                source='liepin',
                title=job['title'],
                company=job['company'],
                location=job['location'],
                description=job['description'],
                url=job['url'],
                salary=job['salary'],
                posted_date=datetime.now().isoformat(),
                raw_data=job
            )
            opportunities.append(op)

        return opportunities

    def _call_liepin_api(self, cfg: dict) -> List[Opportunity]:
        """Real Liepin API call (implement when credentials ready)."""
        # Placeholder for actual API integration
        # Will use: app_key, app_secret, access_token from cfg
        print("[fetch] Liepin API not yet implemented (needs credentials)")
        return []

    def _fetch_zhaopin(self) -> List[Opportunity]:
        """Fetch from 智联 API (mock mode for development)."""
        cfg = self.sources['zhaopin']

        if self.mock_mode:
            print("[fetch] Zhaopin: Using MOCK data (apply for real API)")
            return self._mock_zhaopin_data()

        return []

    def _mock_zhaopin_data(self) -> List[Opportunity]:
        """Generate realistic mock data for Zhaopin."""
        mock_jobs = [
            {
                "title": "AI产品总监",
                "company": "百度",
                "location": "北京",
                "salary": "60-100K",
                "description": "负责百度文库AI重构，推动AI-native产品体验升级。需要10年+产品经验，有成功的AI产品案例。",
                "url": "https://www.zhaopin.com/job/CC123456789.htm"
            },
            {
                "title": "教育科技产品经理",
                "company": "网易有道",
                "location": "北京",
                "salary": "30-50K",
                "description": "负责有道词典笔、听力宝等教育硬件产品的软件功能设计。要求对教育场景有深刻理解，有硬件产品经验加分。",
                "url": "https://www.zhaopin.com/job/CC987654321.htm"
            },
            {
                "title": "AI内容运营专家",
                "company": "小红书",
                "location": "上海",
                "salary": "35-55K",
                "description": "负责小红书AI绘画、AI笔记等功能的运营策略，提升用户创作效率。需要对内容社区和AIGC都有深入理解。",
                "url": "https://www.zhaopin.com/job/CC112233445.htm"
            }
        ]

        opportunities = []
        for job in mock_jobs:
            op_id = f"zhaopin_mock_{hashlib.md5(job['url'].encode()).hexdigest()[:12]}"
            op = Opportunity(
                id=op_id,
                source='zhaopin',
                title=job['title'],
                company=job['company'],
                location=job['location'],
                description=job['description'],
                url=job['url'],
                salary=job['salary'],
                posted_date=datetime.now().isoformat(),
                raw_data=job
            )
            opportunities.append(op)

        return opportunities

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
    fetcher = OpportunityFetcher()
    ops = fetcher.fetch_all()
    print(f"\nTotal fetched: {len(ops)}")
    for op in ops[:5]:
        print(f"- [{op.source}] {op.title} @ {op.company} ({op.location})")
