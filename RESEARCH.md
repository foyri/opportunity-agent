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

## Implementation Recommendations

1.  **Hybrid Data Acquisition**: 
    - Use **Official APIs** for Zhaopin, 51job, and Liepin (structured, reliable).
    - Use **Playwright + Stealth** for BOSS, Lagou, and WeChat (high-value but gated).
2.  **Compliance**: Ensure real-name authentication is completed for API access. Respect non-commercial usage terms.
3.  **Low-Code Integration**: Consider using **Coze** plugins for initial data pulling from platforms with existing plugins.
4.  **Security**: Handle browser fingerprinting carefully for non-API platforms (BOSS, Lagou) to avoid account bans.
