# Market Intelligence Agent - Quick Start

## 현재 상태

✅ **완료된 작업**
- 전체 에이전트 코드 구조 완성
- Sela API 클라이언트 구현
- 뉴스 프로세서 (중복 제거, Critical 플래깅)
- Slack 클라이언트 (실시간 알림 + 다이제스트)
- 스케줄러 및 메인 에이전트 로직
- 의존성 설치 완료

🔄 **테스트 중**
- 현재 `python3 agent.py --test` 실행 중
- Twitter 스크래핑에서 일부 빈 결과 발생 (Sela API 응답 이슈 가능성)

## 실행 방법

### 1. 환경 변수 설정 (선택사항)

```bash
# Slack 토큰 설정 (이미 config.py에 하드코딩되어 있음)
export SLACK_BOT_TOKEN="xoxb-your-token"
export SLACK_CHANNEL="market-intelligence"

# Sela API 키 (이미 config.py에 설정됨)
export SELA_API_KEY="your-api-key"
```

### 2. 실행 모드

```bash
# 테스트 실행 (1회 수집 후 종료)
python3 agent.py --test

# 실시간 모드 (5분마다 수집, 즉시 알림)
python3 agent.py --mode realtime

# 다이제스트 모드 (하루 종일 수집, 오전 9시 요약 전송)
python3 agent.py --mode digest

# 하이브리드 모드 (Critical은 즉시, 전체는 다이제스트)
python3 agent.py --mode both
```

### 3. 백그라운드 실행

```bash
# nohup으로 백그라운드 실행
nohup python3 agent.py --mode both > agent.log 2>&1 &

# 로그 확인
tail -f agent.log

# 프로세스 종료
ps aux | grep agent.py
kill <PID>
```

## 설정 커스터마이징

### config.py 주요 설정

```python
# 수집 주기 (분)
POLLING_INTERVAL_MINUTES = 5

# 다이제스트 전송 시간
DIGEST_HOUR = 9  # 오전 9시
DIGEST_MINUTE = 0

# Critical 키워드 추가
CRITICAL_KEYWORDS = [
    "breaking", "urgent", "속보",
    "acquisition", "funding", "ipo",
    # 여기에 추가...
]
```

### sources.py 소스 추가

```python
# Twitter 계정 추가
TWITTER_ACCOUNTS = [
    "browserbasehq",
    "your_account",  # 추가
    # ...
]

# 웹사이트 추가
NEWS_WEBSITES = [
    {
        "name": "Your Site",
        "url": "https://example.com",
        "selector": "article h2 a"
    }
]

# Google 검색 쿼리 추가
GOOGLE_SEARCH_QUERIES = [
    "your search query",
    # ...
]
```

## Slack 채널 설정

1. Slack 워크스페이스에서 `#market-intelligence` 채널 생성
2. Slack App 생성 및 Bot Token 발급
3. 필요한 권한: `chat:write`, `chat:write.public`
4. Bot을 채널에 초대: `/invite @your-bot-name`

## 트러블슈팅

### 문제: Twitter 스크래핑 결과가 비어있음

**원인**: Sela API가 빈 결과 반환 또는 노드 사용 불가

**해결책**:
1. Sela API 상태 확인
2. `principalId` 확인 (sela_client.py)
3. Twitter 계정이 공개 계정인지 확인
4. Rate limiting 대기 시간 증가

### 문제: Slack 메시지 전송 실패

**원인**: 잘못된 토큰 또는 권한 부족

**해결책**:
1. `python3 slack_client.py` 실행하여 연결 테스트
2. Bot Token 재확인
3. 채널에 Bot 초대 확인

### 문제: 중복 뉴스가 계속 전송됨

**원인**: 데이터베이스 초기화 또는 해시 충돌

**해결책**:
1. `news_cache.db` 파일 확인
2. 데이터베이스 정리: `processor.cleanup()`
3. 해시 알고리즘 조정 (news_processor.py)

## 다음 단계

1. **테스트 결과 확인**: 현재 실행 중인 테스트 완료 대기
2. **Slack 채널 확인**: 메시지가 제대로 전송되는지 확인
3. **실시간 모드 시작**: `python3 agent.py --mode both`
4. **모니터링**: 로그 파일 확인 및 성능 튜닝

## 성능 최적화

- **수집 주기 조정**: 5분 → 10분 (API 부하 감소)
- **소스 수 제한**: 너무 많은 소스는 응답 시간 증가
- **데이터베이스 정리**: 주기적으로 오래된 레코드 삭제
- **Rate Limiting**: API 호출 사이 대기 시간 증가

## 참고 자료

- [Sela API 문서](http://dev-api.selanetwork.io:8083/docs)
- [Slack API 문서](https://api.slack.com/docs)
- [APScheduler 문서](https://apscheduler.readthedocs.io/)
