# Chinese Mainland Platform Analysis

This document provides a technical breakdown of the target hiring platforms in Chinese mainland to guide the implementation of the `opportunity-scan` skill.

## 1. Primary Job Boards

### BOSS直聘 (Boss Zhipin)
*   **Characteristics**: Direct-chat model, highly mobile-centric.
*   **Technical Challenge**: Very high anti-scraping. Uses advanced browser fingerprinting and behavioral analysis.
*   **Strategy**: Use Playwright with `stealth` plugin. Target the web version (`zhipin.com`).
*   **Data Structure**: JSON-like responses in XHR, but often obfuscated.

### 猎聘 (Liepin)
*   **Characteristics**: Focuses on mid-to-high level positions ($100k+ RMB). Good for AI Product roles.
*   **API Access**: ❌ **No personal API available** — enterprise-only
*   **Technical Challenge**: Moderate anti-scraping.
*   **Strategy**: Web scraping with Playwright. Structure is relatively consistent.

### 拉勾网 (Lagou)
*   **Characteristics**: Specifically for tech and internet companies.
*   **Technical Challenge**: Uses custom fonts for salary displays and sometimes other fields to prevent simple scraping.
*   **Strategy**: Need to handle OCR or font-metric mapping if salary data is critical.

## 2. Professional Networking

### 脉脉 (Maimai)
*   **Characteristics**: "LinkedIn for China". Strong for networking and discovering "hidden" opportunities or company internal vibes.
*   **Technical Challenge**: High. Login is usually required for any meaningful data.
*   **Strategy**: Consider as a secondary source or use for "company research" rather than bulk job scanning.

### LinkedIn (China / 领英职场)
*   **Characteristics**: Transitioning into a more local job board. Still useful for international/MNC roles.
*   **Technical Challenge**: Moderate.
*   **Strategy**: Use existing Scraper APIs or Playwright.

## 3. Creative & Niche Platforms

### 小红书 (Xiaohongshu)
*   **Characteristics**: Excellent for photography, design, and "digital nomad" style freelance gigs.
*   **Technical Challenge**: Visual-heavy. Search results are posts (notes).
*   **Strategy**: Keyword search on posts. Need to extract contact info from descriptions or comments (often redirected to WeChat).

### V2EX
*   **Characteristics**: Tech-heavy community. The `/go/jobs` node is high quality.
*   **Technical Challenge**: Low.
*   **Strategy**: RSS feed or simple HTML scraping.

## 4. API & AI Agent Availability Matrix

| 平台名称 | AI Agent 开放情况 | API 个人申请状态 | 个人费用 | 申请难度 | 核心限制 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BOSS直聘** | ✅ 企业端有大模型 | ❌ 不开放个人 API | 企业版 9800+ 元/年 | 极高 | 需企业认证，个人无法申请 |
| **智联招聘** | ✅ AI 招聘助手/智联推荐 | ✅ 个人可申请 | 免费版（基础额度） | 中等 | 需实名认证，非商业用途 |
| **前程无忧** | ✅ AI 求职助手 | ✅ 个人可申请 | 免费版（基础额度） | 中等 | 需实名认证，限流限制 |
| **猎聘** | ✅ 全流程 Agent | ❌ 不开放个人 API | 企业版 9800+ 元/年 | 极高 | 仅企业可申请，个人需用网页抓取 |
| **拉勾招聘** | ✅ AI 智能匹配 | ❌ 不开放个人 API | 企业版 12800+ 元/年 | 极高 | 个人无法申请，反爬严格 |
| **实习僧** | ✅ AI 岗位匹配 | ✅ 个人可申请 | 免费版（限次） | 中等 | 需 IP 白名单及实名认证 |
| **脉脉** | ✅ AI 人才搜索 | ❌ 不开放个人 API | 企业版 2 万+ 元/年 | 极高 | 社交数据不对外，需企业合作 |
| **牛客网** | ✅ AI 面试模拟 | ✅ 个人可申请 | 免费版（基础额度） | 中等 | 个人仅限求职用途 |
| **中华英才网** | ✅ 基础 AI 匹配 | ✅ 个人可申请 | 免费版 | 中等 | 需实名认证，非商业用途 |
| **大街网** | ✅ 基础 AI 匹配 | ❌ 不开放个人 API | 企业版 8800+ 元/年 | 极高 | 平台活跃度低，无个人支持 |

## 5. Platform Technical Strategies

### BOSS直聘 (Boss Zhipin)
*   **Strategy**: No API access. Requires high-fidelity browser automation (Playwright + Stealth).
*   **Agent Integration**: Native Nanbeige model available for enterprise, but opaque for personal agents.

### 智联招聘 (Zhaopin) & 前程无忧 (51job)
*   **Strategy**: **Prioritize Official API**. 
    - Zhaopin requires real-name + face ID. 
    - 51job provides multi-language SDKs (Python/Java).
    - Best for reliable, structured data monitoring without scraping risk.

### 猎聘 (Liepin)
*   **Strategy**: **No personal API available**. Use Playwright-based web scraping.
*   **Note**: Enterprise-only API (9800+ 元/年). Personal users must scrape the website.

### 微信公众号 (WeChat Official Accounts)
*   **Strategy**: 
    - **Sogou WeChat Search**: Use `weixin.sogou.com` for public posts.
    - **RSS-Bridge**: For high-priority official accounts of AI startups.

### 小红书 (Xiaohongshu) & V2EX
*   **Strategy**:
    - **V2EX**: Use RSS feeds or simple HTML parsing for `/go/jobs`.
    - **XHS**: Playwright-based keyword search on post content.

## Web Search Findings (2026-03-04)

### Key Discoveries

1. **智联招聘 (Zhaopin)**
   - Has unofficial/internal APIs used by their web frontend
   - Multiple GitHub projects demonstrate scraping approaches
   - Real-name auth required for any meaningful access
   - Reference: CSDN blogs show API endpoint analysis

2. **BOSS直聘 (Boss Zhipin)**
   - **No official personal API** — enterprise-only via BossHi platform
   - Multiple GitHub projects for automated greeting/resume sending
   - High anti-bot protection with behavioral analysis
   - Reference: Zhihu articles on interface analysis

3. **Alternative Data Sources**
   - **36氪 RSS**: Tech news with hiring announcements
   - **SinoJobs RSS**: International job postings for China
   - **LinkedIn China**: Still operational with RSS support
   - **Company blogs/WeChat**: Many startups post jobs on WeChat first

## Revised Implementation Strategy

### Phase 1 (Immediate - No API Keys Needed)
| Source | Method | Effort | Quality |
|--------|--------|--------|---------|
| V2EX | RSS | Low | High (tech-focused) |
| 36氪 | RSS | Low | Medium (startup jobs) |
| Mock Data | Generator | None | For testing |

### Phase 2 (Requires Setup)
| Source | Method | Prerequisites |
|--------|--------|---------------|
| 智联招聘 | Web scraping OR API | Real-name auth |
| LinkedIn | RSS/API | Account |
| 前程无忧 | Official API | Developer registration |

### Phase 3 (Advanced)
| Source | Method | Notes |
|--------|--------|-------|
| BOSS直聘 | Playwright + Stealth | High maintenance |
| 拉勾网 | OCR + Scraping | Font obfuscation |
| WeChat Search | Sogou scraping | Fragile |

## Compliance & Ethics

1. **Respect robots.txt** on all platforms
2. **Rate limiting**: Max 1 request per 5 seconds
3. **Non-commercial use only** for personal job search
4. **Account safety**: Use dedicated accounts, not main profile

---

## Fresh Web Search Findings (2024-2025 Only)

> Searched with time filter ≤1 year using SerperAPI to ensure current information.

### 智联招聘 (Zhaopin) — 2024-2025 Update
| Metric | Data | Date |
|--------|------|------|
| Database size | 800,000+ postings analyzed in research | Dec 2025 |
| Revenue trend | Declining: 6.35亿 AUD → 5.61亿 AUD (-13.2%) | Aug 2025 |
| AI integration | AI招聘助手 on Baidu AI platform | Apr 2025 |
| API status | Still no open personal API; enterprise-focused | 2025 |

**Verdict**: No change — still requires real-name auth, no developer-friendly API.

### BOSS直聘 — 2024-2025 Update
| Metric | Data | Date |
|--------|------|------|
| Revenue | Growing: 68.07亿元 → 77.61亿元 (+14%) | Aug 2025 |
| AI model | Nanbeige4-3B released (beats Qwen3-32B) | Dec 2025 |
| Anti-bot | Still aggressive; new workarounds published monthly | Dec 2025 |
| API status | No personal API; enterprise-only continues | 2025 |

**Verdict**: Stronger financially, same API restrictions. Scraping remains high-risk.

### 猎聘 (Liepin) — 2024-2025 Update
| Metric | Data | Date |
|--------|------|------|
| Awards | 2024非凡雇主活动 winner | Mar 2025 |
| API status | Enterprise-only (9800+ 元/year) unchanged | 2025 |

**Verdict**: No changes to API policy.

### New Discovery: Get Jobs【AI找工作】— Oct 2025
Found on Zhihu:
- **Tool**: "Get Jobs【工作无忧】"
- **Focus**: 中国大陆招聘平台自动化投递
- **Features**: AI智能匹配 + 定时投递 + 实时通知
- **Note**: Worth investigating as reference implementation

### Industry Trends 2024-2025
- **Anti-bot escalation**: Cloudflare per-customer bot defenses (Sep 2025)
- **Legal framework**: Network data crawling legality standards evolving (Oct 2025 paper)
- **Skill demand**: Web逆向 engineers see 60%+ salary premium (Nov 2025)
- **BOSS dominance**: Revenue growth while 智联 declines suggests market consolidation

### Key Insight
> The landscape hasn't improved for personal API access. If anything, platforms are doubling down on anti-scraping as AI automation threats increase. Hybrid human-AI approach remains optimal strategy.
