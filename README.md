# AI Intelligence

A real-time market intelligence agent for PM teams. Delivers AI, browser automation, and startup news instantly via Slack.

## Features

- **Realtime Mode**: Collects news every 5 minutes, instant alerts for critical items
- **Digest Mode**: Daily summary delivered every morning at 9 AM
- **Critical Flagging**: Auto-tagging based on keywords, source authority, and urgency signals
- **Deduplication**: SQLite-based deduplication to avoid repeat alerts
- **Cross-check**: "Verified" badge when an item is confirmed across multiple sources

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/ai-intelligence.git
cd ai-intelligence

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
# - SELA_API_KEY (required)
# - SLACK_BOT_TOKEN (required)
# - ANTHROPIC_API_KEY or GOOGLE_API_KEY (for AI summaries)

# 4. Run in realtime mode
python agent.py --mode realtime

# Run in digest mode (daily summary)
python agent.py --mode digest

# Run in both modes
python agent.py --mode both

# Test run (single collection)
python agent.py --test
```

## Environment Variables

Create a `.env` file based on `.env.example`:

| Variable | Required | Description |
|----------|----------|-------------|
| `SELA_API_KEY` | ✅ | Sela API key for web scraping |
| `SLACK_BOT_TOKEN` | ✅ | Slack bot token for notifications |
| `SLACK_CHANNEL` | - | Slack channel name (default: `market-intelligence`) |
| `ANTHROPIC_API_KEY` | - | Claude API key for AI summaries |
| `GOOGLE_API_KEY` | - | Google AI API key for AI summaries |
| `AI_PROVIDER` | - | `gemini`, `claude`, or `both` (default: `gemini`) |
| `ENABLE_AI_SUMMARIES` | - | `true` or `false` (default: `true`) |

## Configuration

Additional settings in `config.py`:

| Setting | Description | Default |
|---------|-------------|---------|
| `POLLING_INTERVAL_MINUTES` | News collection interval | 5 min |
| `DIGEST_HOUR` | Daily digest delivery time | 9 AM |
| `CRITICAL_KEYWORDS` | Keywords for critical flagging | Multiple |
| `HIGH_AUTHORITY_SOURCES` | Trusted source list | TechCrunch, etc. |

## Monitored Sources

### Twitter Accounts
- Competitors: @browserbasehq, @browserless, @browser_use
- AI Leaders: @sama, @AndrewYNg, @OpenAI, @AnthropicAI
- VCs: @paulg, @garrytan, @sequoia

### News Sites
- TechCrunch, VentureBeat, Hacker News, The Verge

### Google Search
- Keywords related to browserbase, browserless, AI agents

## Project Structure

```
ai-intelligence/
├── agent.py          # Main agent (scheduler)
├── config.py         # Configuration
├── sources.py        # Monitored sources list
├── sela_client.py    # Sela API client
├── news_processor.py # Deduplication and flagging logic
├── slack_client.py   # Slack delivery
├── requirements.txt  # Dependencies
└── news_cache.db     # SQLite DB (auto-created)
```

## Slack Message Format

### Breaking News (Critical)
```
🔔 Breaking News Alert
🚨 CRITICAL | ✅ Verified
*OpenAI announces GPT-5...*
🐦 @OpenAI • 2024-01-15
_Flags: Keyword: 'openai', High authority account_
```

### Daily Digest
```
📊 Daily Market Digest - 2024-01-15
Summary: 25 items | 🚨 3 critical | ✅ 8 verified

🚨 Critical Items
...

✅ Verified Items
...

📰 Other News
...
```
