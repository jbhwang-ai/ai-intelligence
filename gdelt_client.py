"""
GDELT DOC API Client - 글로벌 뉴스 수집
100+ 언어, 전 세계 뉴스 소스에서 실시간 뉴스를 수집합니다.

지원 기능:
- 키워드 기반 뉴스 검색
- 다국어/다국가 필터링
- 감정 분석 (tone)
- 15분 지연 실시간 데이터
"""
import requests
import time
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote


@dataclass
class NewsItem:
    """뉴스 아이템 (news_aggregator.NewsItem과 호환)"""
    title: str
    url: str
    source: str
    source_type: str
    platform: str = "gdelt"
    timestamp: Optional[str] = None
    author: Optional[str] = None
    content_preview: Optional[str] = None
    # GDELT 추가 필드
    tone: Optional[float] = None  # 감정 점수 (-100 ~ +100)
    language: Optional[str] = None
    source_country: Optional[str] = None


class GDELTClient:
    """GDELT DOC API를 통한 글로벌 뉴스 수집"""

    # GDELT DOC API 기본 URL
    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

    # 언어 코드 매핑
    LANGUAGE_CODES = {
        "en": "english",
        "ko": "korean",
        "ja": "japanese",
        "zh": "chinese",
        "es": "spanish",
        "fr": "french",
        "de": "german",
    }

    # 국가 코드 (FIPS)
    COUNTRY_CODES = {
        "US": "US",
        "KR": "KS",
        "JP": "JA",
        "CN": "CH",
        "UK": "UK",
        "DE": "GM",
        "FR": "FR",
    }

    def __init__(self, default_lang: str = "en", rate_limit_sec: float = 1.0):
        """
        Args:
            default_lang: 기본 언어 (en, ko, ja 등)
            rate_limit_sec: API 요청 간 대기 시간 (초)
        """
        self.default_lang = default_lang
        self.rate_limit_sec = rate_limit_sec
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MarketIntelligenceAgent/1.0"
        })

    def _build_query(
        self,
        keywords: str,
        lang: Optional[str] = None,
        country: Optional[str] = None,
        domain: Optional[str] = None,
        exclude_domain: Optional[str] = None,
    ) -> str:
        """GDELT 쿼리 문자열 생성"""
        query_parts = [keywords]

        # 언어 필터
        if lang:
            lang_code = self.LANGUAGE_CODES.get(lang, lang)
            query_parts.append(f"sourcelang:{lang_code}")

        # 국가 필터
        if country:
            country_code = self.COUNTRY_CODES.get(country, country)
            query_parts.append(f"sourcecountry:{country_code}")

        # 도메인 필터 (특정 소스만)
        if domain:
            query_parts.append(f"domain:{domain}")

        # 도메인 제외
        if exclude_domain:
            query_parts.append(f"-domain:{exclude_domain}")

        return " ".join(query_parts)

    def search(
        self,
        keyword: str,
        lang: Optional[str] = None,
        country: Optional[str] = None,
        timespan: str = "24h",
        max_results: int = 25,
        sort: str = "hybridrel",  # hybridrel (관련성+최신), datedesc (최신순)
        domain: Optional[str] = None,
        exclude_domain: Optional[str] = None,
    ) -> list[NewsItem]:
        """
        키워드로 뉴스 검색

        Args:
            keyword: 검색 키워드 (AND/OR/NOT 연산자 지원)
            lang: 언어 필터 (en, ko, ja 등)
            country: 국가 필터 (US, KR, JP 등)
            timespan: 시간 범위 (15min, 1h, 24h, 7d, 30d)
            max_results: 최대 결과 수 (최대 250)
            sort: 정렬 방식 (hybridrel, datedesc, toneasc, tonedesc)
            domain: 특정 도메인만 검색 (예: techcrunch.com)
            exclude_domain: 특정 도메인 제외

        Returns:
            NewsItem 리스트
        """
        lang = lang or self.default_lang
        query = self._build_query(keyword, lang, country, domain, exclude_domain)

        params = {
            "query": query,
            "mode": "artlist",
            "maxrecords": min(max_results, 250),
            "format": "json",
            "timespan": timespan,
            "sort": sort,
        }

        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()

            # GDELT returns empty response for no results
            if not response.text or response.text.strip() == "":
                return []

            # Check for HTML error page
            if response.text.strip().startswith("<"):
                return []

            data = response.json()
        except requests.exceptions.Timeout:
            print(f"[GDELT] Request timeout for: {keyword[:30]}...")
            return []
        except requests.exceptions.RequestException as e:
            # Network errors - log only if not a common empty response
            if "Expecting value" not in str(e):
                print(f"[GDELT] Network error: {e}")
            return []
        except (ValueError, KeyError):
            # Empty or invalid JSON response (common for no results)
            return []

        articles = data.get("articles", [])
        news_items = []

        for article in articles:
            # 타임스탬프 파싱
            seendate = article.get("seendate", "")
            timestamp = None
            if seendate:
                try:
                    # GDELT 형식: 20240115T120000Z
                    dt = datetime.strptime(seendate, "%Y%m%dT%H%M%SZ")
                    timestamp = dt.isoformat()
                except ValueError:
                    timestamp = seendate

            # 감정 점수 (tone)
            tone = article.get("tone", None)
            if tone:
                try:
                    tone = float(tone)
                except ValueError:
                    tone = None

            news_items.append(NewsItem(
                title=article.get("title", ""),
                url=article.get("url", ""),
                source=f"via {article.get('domain', 'Unknown')}",
                source_type="news",
                platform="gdelt",
                timestamp=timestamp,
                content_preview=article.get("title", ""),  # GDELT는 본문 미제공
                tone=tone,
                language=article.get("language", ""),
                source_country=article.get("sourcecountry", ""),
            ))

        return news_items

    def search_multiple(
        self,
        keywords: list[str],
        lang: Optional[str] = None,
        country: Optional[str] = None,
        timespan: str = "24h",
        max_per_keyword: int = 15,
    ) -> list[NewsItem]:
        """
        여러 키워드로 뉴스 검색

        Args:
            keywords: 키워드 리스트
            lang: 언어 필터
            country: 국가 필터
            timespan: 시간 범위
            max_per_keyword: 키워드당 최대 결과 수

        Returns:
            통합 NewsItem 리스트 (중복 제거됨)
        """
        all_news = []
        seen_urls = set()

        print(f"[GDELT] Searching {len(keywords)} keywords...")

        for keyword in keywords:
            try:
                items = self.search(
                    keyword,
                    lang=lang,
                    country=country,
                    timespan=timespan,
                    max_results=max_per_keyword,
                )

                # 중복 URL 제거
                new_count = 0
                for item in items:
                    if item.url not in seen_urls:
                        seen_urls.add(item.url)
                        all_news.append(item)
                        new_count += 1

                print(f"  - '{keyword}': {len(items)} items ({new_count} new)")
                time.sleep(self.rate_limit_sec)  # Rate limiting

            except Exception as e:
                print(f"  - '{keyword}': Error - {e}")

        print(f"[GDELT] Total: {len(all_news)} unique items")
        return all_news

    def search_by_theme(
        self,
        theme: str,
        timespan: str = "24h",
        max_results: int = 50,
    ) -> list[NewsItem]:
        """
        GDELT 테마로 뉴스 검색

        주요 테마:
        - ECON_BANKRUPTCY: 파산
        - ECON_ENTREPRENEURSHIP: 창업/스타트업
        - ECON_FUNDRAISING: 펀드레이징
        - ECON_MERGER: 인수합병
        - TECH_SCIENCE: 과학기술
        - CYBER_ATTACK: 사이버공격

        Args:
            theme: GDELT 테마 코드
            timespan: 시간 범위
            max_results: 최대 결과 수

        Returns:
            NewsItem 리스트
        """
        query = f"theme:{theme}"
        return self.search(query, timespan=timespan, max_results=max_results)

    def search_competitor(
        self,
        company_name: str,
        timespan: str = "7d",
        max_results: int = 30,
    ) -> list[NewsItem]:
        """
        경쟁사 뉴스 검색

        Args:
            company_name: 회사명 (예: "Browserbase", "Browserless")
            timespan: 시간 범위
            max_results: 최대 결과 수

        Returns:
            NewsItem 리스트
        """
        # 정확한 매칭을 위해 따옴표 사용
        query = f'"{company_name}"'
        return self.search(query, timespan=timespan, max_results=max_results)

    def get_tone_filtered(
        self,
        keyword: str,
        min_tone: Optional[float] = None,
        max_tone: Optional[float] = None,
        timespan: str = "24h",
        max_results: int = 25,
    ) -> list[NewsItem]:
        """
        감정 점수 기반 뉴스 필터링

        Args:
            keyword: 검색 키워드
            min_tone: 최소 감정 점수 (긍정적 뉴스: min_tone=0)
            max_tone: 최대 감정 점수 (부정적 뉴스: max_tone=0)
            timespan: 시간 범위
            max_results: 최대 결과 수

        Returns:
            감정 점수로 필터링된 NewsItem 리스트
        """
        items = self.search(keyword, timespan=timespan, max_results=max_results * 2)

        filtered = []
        for item in items:
            if item.tone is None:
                continue
            if min_tone is not None and item.tone < min_tone:
                continue
            if max_tone is not None and item.tone > max_tone:
                continue
            filtered.append(item)

        return filtered[:max_results]


# 편의 함수
def collect_gdelt_news(
    keywords: list[str],
    lang: str = "en",
    timespan: str = "24h",
) -> list[NewsItem]:
    """키워드 리스트로 GDELT 뉴스 수집 (간편 함수)"""
    client = GDELTClient(default_lang=lang)
    return client.search_multiple(keywords, timespan=timespan)


def collect_competitor_news(
    competitors: list[str],
    timespan: str = "7d",
) -> list[NewsItem]:
    """경쟁사 뉴스 수집 (간편 함수)"""
    client = GDELTClient()
    all_news = []
    seen_urls = set()

    print(f"[GDELT] Searching {len(competitors)} competitors...")

    for company in competitors:
        items = client.search_competitor(company, timespan=timespan)
        for item in items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                all_news.append(item)
        print(f"  - '{company}': {len(items)} items")
        time.sleep(1)

    print(f"[GDELT] Total competitor news: {len(all_news)} unique items")
    return all_news


if __name__ == "__main__":
    # 테스트
    client = GDELTClient()

    print("=== GDELT DOC API Test ===\n")

    # 1. 단일 키워드 검색
    print("1. Single keyword search:")
    items = client.search("AI agent startup", timespan="7d", max_results=5)
    for item in items[:3]:
        print(f"  - {item.title[:60]}...")
        print(f"    Source: {item.source}")
        print(f"    Tone: {item.tone}")
        print()

    # 2. 다중 키워드 검색
    print("2. Multiple keyword search:")
    keywords = ["browser automation", "web scraping AI", "headless browser"]
    items = client.search_multiple(keywords, timespan="7d", max_per_keyword=3)
    print(f"   Total unique items: {len(items)}")
    print()

    # 3. 경쟁사 검색
    print("3. Competitor search:")
    items = client.search_competitor("Browserbase", timespan="30d", max_results=5)
    print(f"   Browserbase news: {len(items)} items")
    for item in items[:2]:
        print(f"  - {item.title[:60]}...")
    print()

    # 4. 긍정적 뉴스 필터링
    print("4. Positive news filter (tone > 0):")
    items = client.get_tone_filtered("AI startup funding", min_tone=0, timespan="7d", max_results=5)
    print(f"   Positive news: {len(items)} items")
    for item in items[:2]:
        print(f"  - {item.title[:50]}... (tone: {item.tone})")
