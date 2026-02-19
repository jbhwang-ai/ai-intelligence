# AI Intelligence - PRD (Product Requirements Document)

**Version:** 1.1.0
**Last Updated:** 2025-01-25
**Author:** Market Intelligence Team

---

## 1. Overview

### 1.1 Product Description
AI Intelligence is an automated agent that collects real-time news, investments, and competitor trends from the AI/automation startup ecosystem and delivers them via Slack.

### 1.2 Goals
- **Real-time Monitoring**: Track competitor and market trends as they happen
- **Information Consolidation**: Aggregate scattered news/social media into a single channel
- **Actionable Insights**: Auto-flag critical news and calculate relevance scores
- **Global Coverage**: 100+ languages, worldwide news sources

### 1.3 Target Users
- Startup founders and executives
- Investment and BD teams
- Product and strategy teams

---

## 2. Functional Requirements

### 2.1 Data Collection

#### 2.1.1 Google News RSS (General News)
| Field | Description |
|-------|-------------|
| **Source** | Google News RSS Feed |
| **Method** | Keyword-based search |
| **Languages** | English, Korean |
| **Time Range** | 1 hour to 7 days |
| **Rate Limit** | 0.5s per request |

#### 2.1.2 GDELT DOC API (Global News)
| Field | Description |
|-------|-------------|
| **Source** | GDELT Project (100+ languages, global sources) |
| **Method** | Keyword + competitor search |
| **Extra Data** | Sentiment (Tone), source country, language |
| **Time Range** | 15 minutes to 30 days |
| **Rate Limit** | 1s per request |
| **Latency** | ~15 minutes |

#### 2.1.3 Sela API (Social Platforms)
| Field | Description |
|-------|-------------|
| **Twitter** | KOL/competitor account monitoring |
| **LinkedIn** | Keyword-based search |
| **Medium** | Tech blog search |
| **Rate Limit** | 2-3s per request |

### 2.2 Data Processing

#### 2.2.1 Deduplication
- URL hash-based duplicate check
- SQLite database storage
- Similar news topic clustering

#### 2.2.2 Relevance Scoring
```
Total Score = (MUST_HAVE keywords × 30pts, cap 60pts)
            + (INTEREST keywords × 10pts, cap 30pts)
            + (Trusted source bonus × 10pts)

Max Score: 100pts
Relevance Threshold: 20pts or above
```

#### 2.2.3 Critical Flagging
An item is flagged as Critical if it meets one or more of the following:
- Contains 1+ MUST_HAVE keywords
- Verified by 3+ independent sources
- Urgency signal (BREAKING) + trusted source

### 2.3 Alert Delivery

#### 2.3.1 Realtime Mode
- Collect every 5 minutes and send to Slack immediately
- Critical news shown first

#### 2.3.2 Digest Mode
- Collect all day, send summary at scheduled time (9 AM)
- Critical news sent immediately

#### 2.3.3 Hybrid Mode
- Critical alerts sent immediately, everything else in daily digest

---

## 3. System Architecture

### 3.1 Components

```
┌─────────────────────────────────────────────────────────────┐
│                  MarketIntelligenceAgent                     │
│                     (agent.py)                               │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌───────────────┐
│  Google News  │   │   GDELT DOC     │   │   Sela API    │
│     RSS       │   │     API         │   │  (Social)     │
│ (news_aggre-  │   │ (gdelt_client.  │   │ (sela_client. │
│  gator.py)    │   │      py)        │   │      py)      │
└───────────────┘   └─────────────────┘   └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                ┌─────────────────────────┐
                │     NewsProcessor       │
                │   (news_processor.py)   │
                │  • Deduplication        │
                │  • Scoring              │
                │  • Critical Flagging    │
                └─────────────────────────┘
                              │
                              ▼
                ┌─────────────────────────┐
                │      NewsDatabase       │
                │   (SQLite - news_       │
                │      cache.db)          │
                └─────────────────────────┘
                              │
                              ▼
                ┌─────────────────────────┐
                │     SlackNewsClient     │
                │   (slack_client.py)     │
                │  • Breaking News        │
                │  • Daily Digest         │
                │  • Batch Update         │
                └─────────────────────────┘
```

### 3.2 File Structure

```
ai-intelligence/
├── agent.py              # Main agent (scheduler)
├── config.py             # Global config (API keys, tokens)
├── sources.py            # Source/keyword management
├── keywords.py           # Filtering keywords (3 tiers)
├── scoring.py            # Scoring rules
│
├── news_aggregator.py    # Google News RSS collector
├── gdelt_client.py       # GDELT DOC API client
├── sela_client.py        # Sela API client
│
├── news_processor.py     # News processing (dedup, scoring, flagging)
├── slack_client.py       # Slack message delivery
│
├── news_cache.db         # SQLite database (auto-created)
├── requirements.txt      # Dependencies
│
└── docs/
    └── PRD.md            # This document
```

### 3.3 Tech Stack

| Category | Technology |
|----------|------------|
| **Language** | Python 3.9+ |
| **Scheduling** | APScheduler 3.10+ |
| **HTTP** | requests 2.31+ |
| **RSS Parsing** | feedparser 6.0+ |
| **HTML Parsing** | BeautifulSoup4 4.12+ |
| **Database** | SQLite3 (built-in) |
| **Notifications** | Slack SDK 3.27+ |

---

## 4. GDELT Integration

### 4.1 GDELT DOC API Overview

GDELT (Global Database of Events, Language, and Tone) is a large-scale open database that monitors and analyzes global news media in real-time.

**Why GDELT:**
- 100+ languages, global coverage
- Free API, no API key required
- Provides sentiment analysis (Tone) data
- Near real-time with ~15 minute delay

### 4.2 API Endpoint

```
Base URL: https://api.gdeltproject.org/api/v2/doc/doc

Parameters:
- query: search terms (AND/OR/NOT supported)
- mode: artlist (article list)
- maxrecords: max results (up to 250)
- format: json
- timespan: time range (15min, 1h, 24h, 7d, 30d)
- sort: hybridrel (relevance+recency), datedesc (newest first)
```

### 4.3 GDELTClient Class

```python
class GDELTClient:
    """GDELT DOC API client"""

    def search(keyword, lang, country, timespan, max_results) -> list[NewsItem]
    def search_multiple(keywords, ...) -> list[NewsItem]
    def search_competitor(company_name, timespan) -> list[NewsItem]
    def get_tone_filtered(keyword, min_tone, max_tone) -> list[NewsItem]
```

### 4.4 Configuration (sources.py)

```python
GDELT_SETTINGS = {
    "enabled": True,
    "languages": ["en"],
    "countries": None,        # None = all countries
    "time_range": "7d",
    "max_per_keyword": 10,
    "rate_limit_sec": 1.0,
}

GDELT_KEYWORDS = [
    "artificial intelligence startup",
    "browser automation",
    "web scraping",
    "startup funding",
    # ...
]

GDELT_COMPETITORS = [
    "Browserbase",
    "Browserless",
    "Browser-Use",
    "Playwright",
    "Puppeteer",
]
```

### 4.5 NewsItem Data Structure

```python
@dataclass
class NewsItem:
    title: str
    url: str
    source: str
    source_type: str
    platform: str = "gdelt"
    timestamp: Optional[str] = None
    content_preview: Optional[str] = None
    # GDELT-specific fields
    tone: Optional[float] = None      # Sentiment score (-100 to +100)
    language: Optional[str] = None
    source_country: Optional[str] = None
```

---

## 5. Keyword Filtering System

### 5.1 Three-Tier Classification

#### MUST_HAVE_KEYWORDS (Auto Critical)
- Competitors: browserbase, browserless, browser-use, stagehand
- Browser automation: playwright, puppeteer, selenium, headless browser
- AI Agent: ai agent, autonomous agent, langchain, crewai
- RPA: rpa, robotic process automation

#### INTEREST_KEYWORDS (Score Boost)
- LLMs: gpt-5, claude, gemini, openai, anthropic
- Tech: chrome extension, webdriver, cdp
- Investment: series a/b/c, funding, acquisition

#### EXCLUDE_KEYWORDS (Filter Out)
- Crypto: crypto price, bitcoin, nft
- Consumer: iphone, android, gaming
- Other: weather, sports, celebrity

### 5.2 Trusted Sources

**News Domains:**
- techcrunch.com, venturebeat.com, theverge.com
- wired.com, reuters.com, bloomberg.com

**Twitter Accounts:**
- sama, AndrewYNg, OpenAI, AnthropicAI
- browserbasehq, browserless

---

## 6. Running the Agent

### 6.1 Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your credentials
```

### 6.2 Commands

```bash
# Test (single collection)
python3 agent.py --test

# Realtime mode (instant alerts every 5 min)
python3 agent.py --mode realtime

# Digest mode (9 AM daily summary)
python3 agent.py --mode digest

# Hybrid (critical instantly + digest)
python3 agent.py --mode both

# Background execution
nohup python3 agent.py --mode both > agent.log 2>&1 &
```

---

## 7. Database Schema

```sql
-- Deduplication & critical tracking
CREATE TABLE seen_news (
    hash_id TEXT PRIMARY KEY,
    title TEXT,
    url TEXT,
    source TEXT,
    source_type TEXT,
    is_critical INTEGER,
    first_seen TIMESTAMP,
    times_seen INTEGER
);

-- Similar news verification (multi-source check)
CREATE TABLE news_topics (
    id INTEGER PRIMARY KEY,
    topic_hash TEXT,
    title TEXT,
    source TEXT,
    timestamp TIMESTAMP
);

CREATE INDEX idx_seen_news_hash ON seen_news(hash_id);
CREATE INDEX idx_news_topics_hash ON news_topics(topic_hash);
```

---

## 8. Roadmap

### Phase 1 - Completed
- [x] Google News RSS integration
- [x] Sela API integration (Twitter, LinkedIn, Medium)
- [x] GDELT DOC API integration
- [x] Deduplication and relevance scoring
- [x] Slack notifications

### Phase 2 - Planned
- [ ] GDELT GKG API integration (entity extraction, advanced sentiment)
- [ ] RSS feed collection (TechCrunch, VentureBeat)
- [ ] Website HTML scraping

### Phase 3 - Future
- [ ] LLM-based news summarization
- [ ] Weekly/monthly trend reports
- [ ] Dashboard UI
- [ ] Multi-channel notifications (beyond Slack)

---

## 9. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-22 | Initial release (Google News + Sela API) |
| 1.1.0 | 2025-01-25 | GDELT DOC API integration |

---

## 10. References

- [GDELT Project](https://www.gdeltproject.org/)
- [GDELT DOC API Documentation](https://blog.gdeltproject.org/gdelt-doc-2-0-api-documentation/)
- [Google News RSS](https://news.google.com/rss)
- [Slack API](https://api.slack.com/)
