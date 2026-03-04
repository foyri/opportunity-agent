# How get_jobs Extracts Job Information

## Technical Architecture (from source code analysis)

### Core Technology Stack
- **Language**: Java (JDK 21)
- **Browser Automation**: Microsoft Playwright
- **Framework**: Spring Boot
- **Database**: MySQL (for blacklist, config, job data)

---

## How They Get Job Info (By Platform)

### BOSS直聘 (Boss.java)

| Aspect | Implementation |
|--------|----------------|
| **Method** | Browser automation via Playwright |
| **Login** | QR code scan (WeChat), cookie persistence |
| **Job Discovery** | Navigate to search URL with keywords + city codes |
| **Scrolling** | Progressive scroll (150% viewport height) until footer appears |
| **Job Cards** | XPath: `//ul[contains(@class, 'rec-job-list')]//li[contains(@class, 'job-card-box')]` |
| **Detail Extraction** | Click card → Intercept API call to `/wapi/zpgeek/job/detail.json` |
| **Anti-Detection** | Random delays, human-like scrolling, cookie rotation |
| **Daily Limit** | ~100-150 chats/day (recently increased from 100) |

**Key Code Pattern**:
```java
// Wait for job detail API response when clicking card
Response detailResp = page.waitForResponse(r -> 
    r.url().contains("/wapi/zpgeek/job/detail.json") && 
    "GET".equalsIgnoreCase(r.request().method()),
    cardToClick::click
);
// Parse JSON response for full job details
```

### 猎聘 (Liepin.java)

| Aspect | Implementation |
|--------|----------------|
| **Method** | Browser automation (similar to BOSS) |
| **Limit** | Unlimited greetings to recruiters (if not initiating chat) |
| **Reliability** | Lower success rate but higher volume |
| **Login** | WeChat QR scan only |

### 51job (Job51.java)

| Aspect | Implementation |
|--------|----------------|
| **Status** | "烂掉了" (broken/low quality) per README |
| **Limit** | Has delivery limits, restricts search results |
| **Recommendation** | Not recommended by project author |

### 智联招聘 (ZhiLian.java)

| Aspect | Implementation |
|--------|----------------|
| **Status** | Currently broken ("平台有问题") |
| **Limit** | ~100 applications/day |
| **Requirement** | Must set default resume (online or attachment) |
| **Login** | WeChat QR scan only |

---

## Key Technical Insights

### 1. Anti-Detection Strategies
- **Random delays** between actions (`PlaywrightUtil.sleep()`)
- **Human-like scrolling** (viewport-based, not instant)
- **Cookie persistence** (weekly re-login via QR scan)
- **Element retry logic** (2 attempts before giving up)
- **No server deployment** (detected and blocked)

### 2. Data Flow
```
1. User scans QR → Cookie saved to DB
2. Search jobs by keyword + city
3. Scroll to load all results (lazy loading)
4. Click each job card
5. Intercept API response for details
6. AI analyze match (optional)
7. Send greeting message (auto-apply)
8. Update database (blacklist, status)
```

### 3. Blacklist System
- Auto-updates from chat responses
- Detects rejection keywords: "不", "感谢", "遗憾", "但"
- Prevents re-applying to same company/recruiter

### 4. AI Integration (Optional)
- Analyzes JD vs user profile
- Generates personalized greeting messages
- Only for BOSS platform currently
- Uses OpenAI-compatible API (configurable base URL)

---

## Critical Findings for Our Project

### What Works
| Platform | Reliability | Volume | Recommendation |
|----------|-------------|--------|----------------|
| BOSS直聘 | High | ~150/day | ✅ Primary target |
| 猎聘 | Medium | Unlimited greetings | ✅ Secondary |
| 51job | Low | Limited | ❌ Skip |
| 智联 | Broken | N/A | ❌ Skip for now |

### Technical Requirements
1. **Playwright/Selenium** — Essential for all platforms
2. **QR Code Login** — All platforms require mobile auth
3. **Cookie Persistence** — Weekly re-auth needed
4. **Rate Limiting** — Strict enforcement, account ban risk
5. **Local Deployment Only** — Server IPs are blocked

### Differences from Our Approach
| Aspect | get_jobs | Our Project |
|--------|----------|-------------|
| **Goal** | Auto-apply (quantity) | Intelligent matching (quality) |
| **Focus** | Greeting automation | Match scoring & analysis |
| **Platforms** | BOSS, 猎聘, 51job, 智联 | V2EX auto + Chinese manual |
| **AI Usage** | Generate greetings | Score matches, suggest angles |
| **Risk Level** | High (aggressive automation) | Lower (hybrid approach) |

---

## Recommendations

### For Our Opportunity Agent

1. **Study Their Implementation**
   - XPath selectors for job cards
   - API interception pattern
   - Anti-detection strategies
   - Cookie management

2. **Differentiate Our Approach**
   - Focus on **analysis**, not application
   - Hybrid model: V2EX auto + Chinese platforms manual
   - Better AI integration (scoring vs just greetings)
   - Calendar tracking, follow-up reminders

3. **Potential Collaboration**
   - Could use their platform modules
   - Add our scoring layer on top
   - Contribute back improvements

### Key Takeaway
> They prove it's **technically possible** to automate Chinese job platforms, but requires:
> - Constant maintenance (anti-bot arms race)
> - Local deployment (no servers)
> - QR login (manual step)
> - Rate limiting respect (or account ban)
>
> Our hybrid approach is **safer and more sustainable**.
