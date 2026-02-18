"""
키워드 관리 파일
이 파일만 수정하면 뉴스 필터링 기준이 변경됩니다.

사용법:
- MUST_HAVE_KEYWORDS: 이 키워드가 포함되면 무조건 Critical로 표시
- INTEREST_KEYWORDS: 이 키워드가 포함되면 관심 뉴스로 표시
- EXCLUDE_KEYWORDS: 이 키워드가 포함되면 필터링 (Slack에 전송 안함)
"""

# =============================================================================
# 🚨 MUST-HAVE KEYWORDS (Critical 표시)
# 이 키워드가 포함된 뉴스는 무조건 Critical로 플래그됩니다
# =============================================================================
MUST_HAVE_KEYWORDS = [
    # --- 직접 경쟁사 ---
    "browserbase",
    "browserless",
    "browser-use",
    "browseruse",
    "stagehand",
    "steel browser",
    "hyperbrowser",

    # --- 브라우저 자동화 기술 ---
    "playwright",
    "puppeteer",
    "selenium",
    "headless browser",
    "headless chrome",
    "browser automation",
    "web automation",
    "web scraping",
    "web crawler",

    # --- AI Agent 핵심 ---
    "ai agent",
    "autonomous agent",
    "agentic ai",
    "agent framework",
    "multi-agent",
    "langchain",
    "langgraph",
    "crewai",
    "autogen",
    "autogpt",
    "openai agent",
    "claude computer use",

    # --- RPA/자동화 ---
    "rpa",
    "robotic process automation",
    "workflow automation",

    # --- Sela 직접 관련 ---
    "sela network",
    "decentralized scraping",
    "distributed scraping",
]

# =============================================================================
# ⭐ INTEREST KEYWORDS (관심 뉴스)
# 이 키워드가 포함된 뉴스는 중요도가 높아집니다
# =============================================================================
INTEREST_KEYWORDS = [
    # --- AI Infrastructure ---
    "llm infrastructure",
    "inference",
    "fine-tuning",
    "fine tuning",
    "rag",
    "retrieval augmented",
    "vector database",
    "embedding",
    "prompt engineering",

    # --- LLM 모델 ---
    "gpt-5",
    "gpt-4",
    "claude",
    "gemini",
    "llama",
    "mistral",
    "openai",
    "anthropic",

    # --- 브라우저/웹 기술 ---
    "chrome extension",
    "webdriver",
    "cdp",
    "devtools protocol",
    "chromium",

    # --- 스타트업/투자 ---
    "series a",
    "series b",
    "series c",
    "funding",
    "raised",
    "acquisition",
    "acquired",
    "y combinator",
    "yc",
    "a16z",
    "andreessen",
    "sequoia",

    # --- 시장 동향 ---
    "partnership",
    "launch",
    "announces",
    "released",
    "open source",
    "open-source",
]

# =============================================================================
# 🚫 EXCLUDE KEYWORDS (필터링 - 전송 안함)
# 이 키워드가 포함된 뉴스는 Slack에 전송되지 않습니다
# =============================================================================
EXCLUDE_KEYWORDS = [
    # --- 관련 없는 Crypto/Web3 ---
    "crypto price",
    "bitcoin price",
    "ethereum price",
    "token price",
    "nft",
    "memecoin",
    "defi yield",

    # --- 소비자 테크 ---
    "iphone",
    "android app",
    "smartphone",
    "gaming",
    "playstation",
    "xbox",
    "nintendo",

    # --- 엔터테인먼트 ---
    "movie",
    "tv show",
    "netflix",
    "spotify",
    "streaming",

    # --- 기타 무관 ---
    "weather",
    "sports",
    "celebrity",
]

# =============================================================================
# 🏢 HIGH AUTHORITY SOURCES (신뢰 소스)
# 이 소스에서 온 뉴스는 신뢰도가 높아집니다
# =============================================================================
HIGH_AUTHORITY_DOMAINS = [
    "techcrunch.com",
    "venturebeat.com",
    "theverge.com",
    "wired.com",
    "arstechnica.com",
    "reuters.com",
    "bloomberg.com",
    "browserbase.com",
    "browserless.io",
]

HIGH_AUTHORITY_TWITTER = [
    "sama",           # Sam Altman
    "AndrewYNg",      # Andrew Ng
    "OpenAI",         # OpenAI
    "AnthropicAI",    # Anthropic
    "LangChainAI",    # LangChain
    "browserbasehq",  # Browserbase
    "browserless",    # Browserless
    "browser_use",    # Browser-Use
]
