"""
뉴스 소스 관리 파일
플랫폼별 모니터링 설정을 여기서 관리합니다.

=== 하이브리드 수집 구조 ===

1. 일반 뉴스 (Google News RSS)
   - 키워드 기반으로 수천 개 소스에서 자동 수집
   - 플랫폼/사이트 관리 불필요

2. 소셜 플랫폼 (Sela API)
   - Twitter: KOL/경쟁사 계정 모니터링
   - LinkedIn: 키워드 검색
   - Medium: 키워드 검색
"""

# =============================================================================
# 📰 Google News 키워드 (일반 뉴스 수집)
# 이 키워드들로 수천 개 뉴스 소스에서 자동 수집됩니다
# =============================================================================

GOOGLE_NEWS_KEYWORDS = [
    # --- AI Agent & Automation (넓은 키워드) ---
    "AI agent",
    "agentic AI",
    "autonomous AI agent",
    "AI automation",

    # --- Browser/Web Automation ---
    "browser automation",
    "web automation",
    "web scraping",
    "headless browser",
    "RPA AI automation",

    # --- AI Infrastructure ---
    "AI infrastructure",
    "LLM",
    "AI developer tools",

    # --- 투자/시장 ---
    "AI startup Series A",
    "automation startup funding",
    "startup funding",
    "enterprise AI funding",
    "ai trends",
]

# Google News 설정 (RSS 기반)
GOOGLE_NEWS_SETTINGS = {
    "enabled": True,  # 활성화
    "languages": ["en"],      # 언어 (en, ko)
    "time_range": "1d",       # 시간 범위 (1h, 1d, 7d)
    "max_per_keyword": 10,    # 키워드당 최대 결과
}

# =============================================================================
# 🔍 Sela Google News 설정 (HTML 스크래핑 기반 - 최신순)
# RSS보다 더 풍부한 메타데이터, 최신순 정렬 지원
# =============================================================================

SELA_GOOGLE_NEWS_SETTINGS = {
    "enabled": True,           # Sela API를 통한 Google News 스크래핑
    "time_range": "1d",        # 시간 범위 (1h, 1d, 7d, 1m)
    "max_per_keyword": 50,     # 키워드당 최대 결과
    "lang": "en",              # 언어 (en, ko)
    "rate_limit_sec": 30,      # 키워드 간 대기 시간 (캡챠 회피)
    "mode": "round_robin",     # 모드: "batch" 또는 "round_robin"
    "keywords_per_cycle": 2,   # 라운드 로빈: 주기당 처리할 키워드 수
    # batch 모드 설정 (deprecated)
    "batch_size": 4,
    "batch_delay_sec": 30,
}

# Sela Google News 전용 키워드 (넓은 검색으로 더 많은 결과)
SELA_GOOGLE_NEWS_KEYWORDS = [
    "AI agent",
    "agentic AI",
    "autonomous AI agent",
    "AI automation",

    # --- Browser/Web Automation ---
    "browser automation",
    "web automation",
    "web scraping",
    "headless browser",
    "RPA AI automation",

    # --- AI Infrastructure ---
    "AI infrastructure",
    "LLM",
    "AI developer tools",

    # --- 투자/시장 ---
    "AI startup Series A",
    "automation startup funding",
    "startup funding",
    "enterprise AI funding",
    "ai trends",

    # --- 기술 트렌드 ---
    "OpenAI",
    "Anthropic",
    "LLM",

    # --- 경쟁사 ---
    "Browserbase",
    "Browserless",
    "Browser-Use",
    "tavily",
    "brightdata",
]

# =============================================================================
# 🌍 GDELT 설정 (글로벌 뉴스)
# 100+ 언어, 전 세계 뉴스 소스에서 수집
# =============================================================================

GDELT_SETTINGS = {
    "enabled": False,  # Sela 테스트를 위해 비활성화
    "languages": ["en"],      # 언어 필터 (en, ko, ja 등)
    "countries": None,        # 국가 필터 (US, KR 등), None=전체
    "time_range": "7d",       # 시간 범위 (15min, 1h, 24h, 7d, 30d) - 7d 권장
    "max_per_keyword": 10,    # 키워드당 최대 결과
    "rate_limit_sec": 1.0,    # API 요청 간 대기 시간
}

# GDELT 전용 키워드 (Google News와 다른 글로벌/투자 중심)
# 참고: GDELT는 넓은 키워드가 더 효과적
GDELT_KEYWORDS = [
    # --- AI/자동화 (넓은 키워드) ---
    "artificial intelligence startup",
    "browser automation",
    "web scraping",
    "AI agent",

    # --- 투자/펀딩 ---
    "startup funding",
    "series A funding",
    "AI investment",

    # --- M&A / 파트너십 ---
    "tech acquisition",
    "AI company merger",
    "enterprise software partnership",
]

# GDELT 경쟁사 모니터링 (별도 추적)
GDELT_COMPETITORS = [
    "Browserbase",
    "Browserless",
    "Browser-Use",
    "Playwright",
    "Puppeteer",
]

# GDELT 테마 필터 (선택적)
# 참고: https://blog.gdeltproject.org/gdelt-2-0-our-global-world-in-realtime/
GDELT_THEMES = [
    "ECON_ENTREPRENEURSHIP",  # 창업/스타트업
    "ECON_FUNDRAISING",       # 펀드레이징
    "ECON_MERGER",            # 인수합병
    "ECON_BANKRUPTCY",        # 파산 (경쟁사 모니터링)
]

# =============================================================================
# 🐦 Twitter 설정 (Sela API)
# =============================================================================

# 모니터링할 Twitter 계정 (KOL, 경쟁사, 뉴스 등)
TWITTER_ACCOUNTS = [
    # --- 경쟁사 ---
    "browserbasehq",    # Browserbase
    "browserless",      # Browserless
    "browser_use",      # Browser-Use

    # --- AI 리더 ---
    "sama",             # Sam Altman, OpenAI CEO
    "AndrewYNg",        # Andrew Ng
    "karpathy",         # Andrej Karpathy
    "ylecun",           # Yann LeCun

    # --- AI 기업 ---
    "OpenAI",
    "AnthropicAI",
    "LangChainAI",
    "crewAIInc",

    # --- VC/스타트업 ---
    "paulg",            # Paul Graham
    "garrytan",         # Garry Tan, YC CEO
]

# Twitter 검색 키워드 (추후 Twitter Search API 지원 시 사용)
TWITTER_KEYWORDS = [
    "browser automation",
    "AI agent",
    "web scraping",
    "headless browser",
]

# =============================================================================
# 💼 LinkedIn 설정
# =============================================================================

# LinkedIn 검색 키워드
LINKEDIN_KEYWORDS = [
    "browser automation AI",
    "web scraping startup",
    "AI agent framework",
    "headless browser",
    "RPA automation",
    "playwright puppeteer",
]

# =============================================================================
# 📝 Medium 설정
# =============================================================================

# Medium 검색 키워드
MEDIUM_KEYWORDS = [
    "browser automation",
    "AI agents",
    "web scraping python",
    "playwright tutorial",
    "puppeteer automation",
    "LangChain agents",
    "autonomous AI",
]

# =============================================================================
# 🌐 웹사이트 (HTML 스크래핑)
# =============================================================================

NEWS_WEBSITES = [
    # --- 테크 뉴스 ---
    {
        "name": "Hacker News",
        "url": "https://news.ycombinator.com/",
        "category": "tech_community",
        "priority": "high",
    },
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/",
        "category": "tech_news",
        "priority": "high",
    },

    # --- 경쟁사 블로그 ---
    {
        "name": "Browserbase Blog",
        "url": "https://www.browserbase.com/blog",
        "category": "competitor",
        "priority": "critical",
    },
    {
        "name": "Browserless Blog",
        "url": "https://www.browserless.io/blog",
        "category": "competitor",
        "priority": "critical",
    },

    # --- AI/Agent 전문 ---
    {
        "name": "LangChain Blog",
        "url": "https://blog.langchain.dev/",
        "category": "ai_agent",
        "priority": "high",
    },
]

# =============================================================================
# 🔍 Google 검색 쿼리
# =============================================================================

GOOGLE_SEARCH_QUERIES = [
    # 경쟁사
    "browserbase news",
    "browserless news",
    "browser-use AI",

    # 기술 트렌드
    "browser automation AI agent 2024",
    "headless browser startup funding",
    "web scraping AI news",

    # 시장
    "AI agent framework funding",
    "RPA market news",
]

# =============================================================================
# 📊 플랫폼별 수집 설정
# =============================================================================

# 각 플랫폼별 활성화 여부
PLATFORM_SETTINGS = {
    "twitter": {
        "enabled": False,        # Sela API 비활성화
        "post_count": 10,
        "rate_limit_sec": 2,
    },
    "linkedin": {
        "enabled": False,        # Sela API 비활성화
        "post_count": 10,
        "rate_limit_sec": 3,
    },
    "medium": {
        "enabled": False,        # Sela API 비활성화
        "article_count": 15,
        "rate_limit_sec": 2,
    },
    "website": {
        "enabled": True,
        "max_items": 30,
        "rate_limit_sec": 2,
    },
    "google": {
        "enabled": True,
        "results_per_query": 10,
        "rate_limit_sec": 3,
    },
    "sela_google_news": {
        "enabled": True,         # Sela API로 Google News 스크래핑 (최신순)
        "max_per_keyword": 10,
        "time_range": "1d",
        "rate_limit_sec": 2,
    },
}


# =============================================================================
# 🚫 Sela API 미지원 플랫폼 대안
# =============================================================================

"""
Sela API에서 지원하지 않는 플랫폼의 경우 다음 대안을 고려하세요:

1. RSS 피드 (무료, 안정적)
   - TechCrunch: https://techcrunch.com/feed/
   - VentureBeat: https://venturebeat.com/feed/
   - Hacker News: https://hnrss.org/newest
   - Product Hunt: https://www.producthunt.com/feed

2. 공식 API (API 키 필요)
   - Twitter API v2 (유료)
   - Reddit API
   - YouTube Data API
   - Discord Webhooks

3. 뉴스레터 구독 후 이메일 파싱
   - Ben's Bites (AI)
   - TLDR Newsletter
   - The Rundown AI

4. Webhook/Alert 서비스
   - Google Alerts
   - Mention.com
   - Brand24
"""

# RSS 피드 (선택적 사용)
RSS_FEEDS = [
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "category": "tech_news",
    },
    {
        "name": "Hacker News RSS",
        "url": "https://hnrss.org/newest",
        "category": "tech_community",
    },
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/",
        "category": "ai_news",
    },
]
