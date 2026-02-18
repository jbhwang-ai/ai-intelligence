# Market Intelligence Agent

PM팀을 위한 실시간 마켓 인텔리전스 에이전트. Slack을 통해 AI, 브라우저 자동화, 스타트업 뉴스를 실시간으로 전달합니다.

## Features

- **실시간 모드**: 5분마다 뉴스 수집, 중요 뉴스 즉시 알림
- **다이제스트 모드**: 매일 오전 9시 요약 전달
- **Critical 플래깅**: 키워드, 소스 권위도, 긴급 시그널 기반 자동 태깅
- **중복 제거**: SQLite 기반 deduplication
- **Cross-check**: 다중 소스 검증 시 "Verified" 배지

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/market-intelligence-agent.git
cd market-intelligence-agent

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

| 설정 | 설명 | 기본값 |
|------|------|--------|
| `POLLING_INTERVAL_MINUTES` | 수집 주기 | 5분 |
| `DIGEST_HOUR` | 다이제스트 전송 시간 | 9시 |
| `CRITICAL_KEYWORDS` | Critical 플래깅 키워드 | 다수 |
| `HIGH_AUTHORITY_SOURCES` | 신뢰 소스 목록 | TechCrunch 등 |

## 모니터링 소스

### Twitter 계정
- 경쟁사: @browserbasehq, @browserless, @browser_use
- AI 리더: @sama, @AndrewYNg, @OpenAI, @AnthropicAI
- VC: @paulg, @garrytan, @sequoia

### 뉴스 사이트
- TechCrunch, VentureBeat, Hacker News, The Verge

### Google 검색
- browserbase, browserless, AI agent 관련 키워드

## 프로젝트 구조

```
market-intelligence-agent/
├── agent.py          # 메인 에이전트 (스케줄러)
├── config.py         # 설정
├── sources.py        # 모니터링 소스 목록
├── sela_client.py    # Sela API 클라이언트
├── news_processor.py # 중복제거, 플래깅 로직
├── slack_client.py   # Slack 전송
├── requirements.txt  # 의존성
└── news_cache.db     # SQLite DB (자동 생성)
```

## Slack 메시지 형식

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
