"""
Configuration for Market Intelligence Agent
"""
import os

# Sela API Configuration
SELA_API_BASE_URL = os.getenv("SELA_API_BASE_URL", "http://dev-api.selanetwork.io:8083")
SELA_API_KEY = os.getenv("SELA_API_KEY")

# Slack Configuration
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "market-intelligence")

# AI Summarization Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")  # "gemini", "claude", or "both"
ENABLE_AI_SUMMARIES = os.getenv("ENABLE_AI_SUMMARIES", "true").lower() == "true"

# Polling Configuration
POLLING_INTERVAL_MINUTES = 10

# Database Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), "news_cache.db")

# Critical Flagging Keywords
CRITICAL_KEYWORDS = [
    # Urgency signals
    "breaking", "just in", "urgent", "속보", "긴급", "exclusive",
    # High-impact events
    "acquisition", "acquired", "funding", "raised", "series a", "series b", "series c",
    "ipo", "partnership", "launch", "released", "announces",
    # Regulatory
    "sec", "regulation", "regulatory", "lawsuit", "legal", "compliance", "ban", "banned",
    # Security
    "hack", "hacked", "breach", "exploit", "vulnerability", "security incident",
    # Market impact
    "shutdown", "bankrupt", "layoff", "layoffs", "pivot",
    # Competitor specific
    "browserbase", "browserless", "browser-use", "browseruse",
    # Tech trends
    "gpt-5", "claude", "gemini", "llama", "openai", "anthropic", "google ai",
    "ai agent", "autonomous agent", "browser automation",
]

# High Authority Sources (for critical flagging)
HIGH_AUTHORITY_SOURCES = [
    "techcrunch.com",
    "venturebeat.com",
    "theverge.com",
    "wired.com",
    "arstechnica.com",
    "reuters.com",
    "bloomberg.com",
]

# High Authority Twitter Accounts
HIGH_AUTHORITY_TWITTER = [
    "sama",           # Sam Altman
    "elonmusk",       # Elon Musk
    "OpenAI",         # OpenAI
    "AnthropicAI",    # Anthropic
    "googleai",       # Google AI
    "browserbasehq",  # Browserbase
    "browserless",    # Browserless
    "browser_use",    # Browser-Use
]

# Digest Configuration
DIGEST_HOUR = 9  # 9 AM
DIGEST_MINUTE = 0
