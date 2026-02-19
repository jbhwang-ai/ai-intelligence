# AI Intelligence - PRD (Product Requirements Document)

**Version:** 1.1.0
**Last Updated:** 2025-01-25
**Author:** Market Intelligence Team

---

## 1. 개요

### 1.1 제품 설명
AI Intelligence는 AI/자동화 스타트업 생태계의 뉴스, 투자, 경쟁사 동향을 실시간으로 수집하고 Slack으로 전달하는 자동화 에이전트입니다.

### 1.2 목표
- **실시간 모니터링**: 경쟁사 및 시장 동향을 실시간으로 파악
- **정보 통합**: 분산된 뉴스/소셜 미디어 정보를 단일 채널로 통합
- **인사이트 제공**: Critical 뉴스 자동 플래깅 및 관련도 점수 계산
- **글로벌 커버리지**: 100+ 언어, 전 세계 뉴스 소스 커버

### 1.3 대상 사용자
- 스타트업 창업자/경영진
- 투자팀/BD팀
- 제품/전략팀

---

## 2. 기능 요구사항

### 2.1 데이터 수집

#### 2.1.1 Google News RSS (일반 뉴스)
| 항목 | 설명 |
|------|------|
| **소스** | Google News RSS Feed |
| **수집 방식** | 키워드 기반 검색 |
| **언어** | 영어, 한국어 지원 |
| **시간 범위** | 1시간 ~ 7일 |
| **Rate Limit** | 0.5초/요청 |

#### 2.1.2 GDELT DOC API (글로벌 뉴스)
| 항목 | 설명 |
|------|------|
| **소스** | GDELT Project (100+ 언어, 전 세계 소스) |
| **수집 방식** | 키워드 + 경쟁사 검색 |
| **추가 데이터** | 감정 분석(Tone), 소스 국가, 언어 |
| **시간 범위** | 15분 ~ 30일 |
| **Rate Limit** | 1초/요청 |
| **지연 시간** | 약 15분 |

#### 2.1.3 Sela API (소셜 플랫폼)
| 항목 | 설명 |
|------|------|
| **Twitter** | KOL/경쟁사 계정 모니터링 |
| **LinkedIn** | 키워드 기반 검색 |
| **Medium** | 기술 블로그 검색 |
| **Rate Limit** | 2-3초/요청 |

### 2.2 데이터 처리

#### 2.2.1 중복 제거
- URL 해시 기반 중복 체크
- SQLite 데이터베이스 저장
- 유사 뉴스 토픽 클러스터링

#### 2.2.2 관련도 점수 계산
```
총점 = (MUST_HAVE 키워드 × 30점, 상한 60점)
     + (INTEREST 키워드 × 10점, 상한 30점)
     + (신뢰 소스 보너스 × 10점)

최대 점수: 100점
관련성 기준: 20점 이상
```

#### 2.2.3 Critical 플래깅
다음 조건 중 하나 이상 충족 시 Critical로 표시:
- MUST_HAVE 키워드 1개 이상 포함
- 다중 소스 3개 이상에서 검증
- 긴급 신호(BREAKING) + 신뢰 소스

### 2.3 알림 전달

#### 2.3.1 실시간 모드 (realtime)
- 5분마다 수집 및 즉시 Slack 전송
- Critical 뉴스 우선 표시

#### 2.3.2 다이제스트 모드 (digest)
- 하루 종일 수집, 지정 시간(오전 9시)에 요약 전송
- Critical 뉴스는 즉시 전송

#### 2.3.3 하이브리드 모드 (both)
- Critical은 즉시, 전체는 다이제스트

---

## 3. 시스템 아키텍처

### 3.1 구성 요소

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
                │  • 중복 제거            │
                │  • 점수 계산            │
                │  • Critical 플래깅      │
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

### 3.2 파일 구조

```
ai-intelligence/
├── agent.py              # 메인 에이전트 (스케줄러)
├── config.py             # 전역 설정 (API 키, 토큰)
├── sources.py            # 소스/키워드 관리
├── keywords.py           # 필터링 키워드 (3단계)
├── scoring.py            # 점수 계산 규칙
│
├── news_aggregator.py    # Google News RSS 수집
├── gdelt_client.py       # GDELT DOC API 클라이언트
├── sela_client.py        # Sela API 클라이언트
│
├── news_processor.py     # 뉴스 처리 (중복, 점수, 플래깅)
├── slack_client.py       # Slack 메시지 전송
│
├── news_cache.db         # SQLite 데이터베이스
├── requirements.txt      # 의존성
│
└── docs/
    └── PRD.md            # 이 문서
```

### 3.3 기술 스택

| 분류 | 기술 |
|------|------|
| **언어** | Python 3.9+ |
| **스케줄링** | APScheduler 3.10+ |
| **HTTP** | requests 2.31+ |
| **RSS 파싱** | feedparser 6.0+ |
| **HTML 파싱** | BeautifulSoup4 4.12+ |
| **데이터베이스** | SQLite3 (내장) |
| **알림** | Slack SDK 3.27+ |

---

## 4. GDELT 통합 상세

### 4.1 GDELT DOC API 개요

GDELT(Global Database of Events, Language, and Tone)는 전 세계 뉴스 미디어를 실시간으로 모니터링하고 분석하는 대규모 오픈 데이터베이스입니다.

**선택 이유:**
- 100+ 언어, 글로벌 커버리지
- 무료 API, API 키 불필요
- 감정 분석(Tone) 데이터 제공
- 15분 지연으로 거의 실시간

### 4.2 API 엔드포인트

```
Base URL: https://api.gdeltproject.org/api/v2/doc/doc

Parameters:
- query: 검색어 (AND/OR/NOT 지원)
- mode: artlist (기사 목록)
- maxrecords: 최대 결과 수 (최대 250)
- format: json
- timespan: 시간 범위 (15min, 1h, 24h, 7d, 30d)
- sort: hybridrel (관련성+최신), datedesc (최신순)
```

### 4.3 GDELTClient 클래스

```python
class GDELTClient:
    """GDELT DOC API 클라이언트"""

    def search(keyword, lang, country, timespan, max_results) -> list[NewsItem]
    def search_multiple(keywords, ...) -> list[NewsItem]
    def search_competitor(company_name, timespan) -> list[NewsItem]
    def get_tone_filtered(keyword, min_tone, max_tone) -> list[NewsItem]
```

### 4.4 설정 (sources.py)

```python
GDELT_SETTINGS = {
    "enabled": True,
    "languages": ["en"],
    "countries": None,        # None = 전체
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

### 4.5 NewsItem 데이터 구조

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
    # GDELT 추가 필드
    tone: Optional[float] = None      # 감정 점수 (-100 ~ +100)
    language: Optional[str] = None
    source_country: Optional[str] = None
```

---

## 5. 키워드 필터링 체계

### 5.1 3단계 분류

#### MUST_HAVE_KEYWORDS (Critical 자동 표시)
- 경쟁사: browserbase, browserless, browser-use, stagehand
- 브라우저 자동화: playwright, puppeteer, selenium, headless browser
- AI Agent: ai agent, autonomous agent, langchain, crewai
- RPA: rpa, robotic process automation

#### INTEREST_KEYWORDS (점수 증가)
- LLM: gpt-5, claude, gemini, openai, anthropic
- 기술: chrome extension, webdriver, cdp
- 투자: series a/b/c, funding, acquisition

#### EXCLUDE_KEYWORDS (필터링)
- Crypto: crypto price, bitcoin, nft
- 소비자: iphone, android, gaming
- 기타: weather, sports, celebrity

### 5.2 신뢰 소스

**뉴스 도메인:**
- techcrunch.com, venturebeat.com, theverge.com
- wired.com, reuters.com, bloomberg.com

**Twitter 계정:**
- sama, AndrewYNg, OpenAI, AnthropicAI
- browserbasehq, browserless

---

## 6. 실행 가이드

### 6.1 환경 설정

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 (선택적)
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_CHANNEL="market-intelligence"
```

### 6.2 실행 명령어

```bash
# 테스트 (1회 수집)
python3 agent.py --test

# 실시간 모드 (5분마다 즉시 알림)
python3 agent.py --mode realtime

# 다이제스트 모드 (오전 9시 요약)
python3 agent.py --mode digest

# 하이브리드 (Critical 즉시 + 다이제스트)
python3 agent.py --mode both

# 백그라운드 실행
nohup python3 agent.py --mode both > agent.log 2>&1 &
```

---

## 7. 데이터베이스 스키마

```sql
-- 중복 추적 & Critical 기록
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

-- 유사 뉴스 검증 (다중 소스 체크)
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

## 8. 향후 계획

### Phase 1 - 완료
- [x] Google News RSS 통합
- [x] Sela API 통합 (Twitter, LinkedIn, Medium)
- [x] GDELT DOC API 통합
- [x] 중복 제거 및 점수 계산
- [x] Slack 알림

### Phase 2 - 계획
- [ ] GDELT GKG API 통합 (엔티티 추출, 고급 감정 분석)
- [ ] RSS 피드 수집 (TechCrunch, VentureBeat)
- [ ] 웹사이트 HTML 스크래핑

### Phase 3 - 고도화
- [ ] LLM 기반 뉴스 요약
- [ ] 주간/월간 트렌드 리포트
- [ ] 대시보드 UI
- [ ] 알림 커스터마이징 (Slack 외 채널)

---

## 9. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0.0 | 2025-01-22 | 초기 버전 (Google News + Sela API) |
| 1.1.0 | 2025-01-25 | GDELT DOC API 통합 |

---

## 10. 참고 자료

- [GDELT Project](https://www.gdeltproject.org/)
- [GDELT DOC API Documentation](https://blog.gdeltproject.org/gdelt-doc-2-0-api-documentation/)
- [Google News RSS](https://news.google.com/rss)
- [Slack API](https://api.slack.com/)
