"""
News Aggregator - Google News RSS 기반 뉴스 수집
키워드만 설정하면 수천 개 소스에서 자동으로 뉴스를 수집합니다.

지원 기능:
- 키워드 기반 뉴스 검색
- 다국어 지원 (한국어, 영어 등)
- 시간순 정렬
- 소스/플랫폼 독립적
"""
import feedparser
import time
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote


@dataclass
class NewsItem:
    """뉴스 아이템 (sela_client.NewsItem과 호환)"""
    title: str
    url: str
    source: str
    source_type: str
    platform: str = "google_news"
    timestamp: Optional[str] = None
    author: Optional[str] = None
    content_preview: Optional[str] = None


class GoogleNewsAggregator:
    """Google News RSS를 통한 뉴스 수집"""

    # Google News RSS 기본 URL
    BASE_URL = "https://news.google.com/rss/search"

    # 언어/지역 설정
    LOCALES = {
        "en": {"hl": "en-US", "gl": "US", "ceid": "US:en"},
        "ko": {"hl": "ko", "gl": "KR", "ceid": "KR:ko"},
    }

    def __init__(self, default_lang: str = "en"):
        self.default_lang = default_lang

    def _build_url(self, query: str, lang: str = None, when: str = None) -> str:
        """RSS 피드 URL 생성"""
        lang = lang or self.default_lang
        locale = self.LOCALES.get(lang, self.LOCALES["en"])

        # 시간 필터 (1h, 1d, 7d 등)
        time_filter = f"+when:{when}" if when else ""

        encoded_query = quote(f"{query}{time_filter}")
        url = f"{self.BASE_URL}?q={encoded_query}&hl={locale['hl']}&gl={locale['gl']}&ceid={locale['ceid']}"

        return url

    def search(self, keyword: str, lang: str = None, when: str = "1d", max_results: int = 20) -> list[NewsItem]:
        """
        키워드로 뉴스 검색

        Args:
            keyword: 검색 키워드
            lang: 언어 (en, ko)
            when: 시간 필터 (1h, 1d, 7d)
            max_results: 최대 결과 수

        Returns:
            NewsItem 리스트
        """
        url = self._build_url(keyword, lang, when)

        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"[GoogleNews] Error fetching feed: {e}")
            return []

        news_items = []
        for entry in feed.entries[:max_results]:
            # 소스 추출 (Google News 형식: "Title - Source")
            title = entry.get("title", "")
            source = "Unknown"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                if len(parts) == 2:
                    title = parts[0]
                    source = parts[1]

            # 발행 시간
            published = entry.get("published", "")

            news_items.append(NewsItem(
                title=title,
                url=entry.get("link", ""),
                source=f"via {source}",
                source_type="news",
                platform="google_news",
                timestamp=published,
                content_preview=entry.get("summary", "")[:500] if entry.get("summary") else None
            ))

        return news_items

    def search_multiple(self, keywords: list[str], lang: str = None, when: str = "1d", max_per_keyword: int = 10) -> list[NewsItem]:
        """
        여러 키워드로 뉴스 검색

        Args:
            keywords: 키워드 리스트
            lang: 언어
            when: 시간 필터
            max_per_keyword: 키워드당 최대 결과 수

        Returns:
            통합 NewsItem 리스트
        """
        all_news = []
        seen_urls = set()

        print(f"[GoogleNews] Searching {len(keywords)} keywords...")

        for keyword in keywords:
            try:
                items = self.search(keyword, lang, when, max_per_keyword)

                # 중복 URL 제거
                for item in items:
                    if item.url not in seen_urls:
                        seen_urls.add(item.url)
                        all_news.append(item)

                print(f"  - '{keyword}': {len(items)} items")
                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                print(f"  - '{keyword}': Error - {e}")

        print(f"[GoogleNews] Total: {len(all_news)} unique items")
        return all_news

    def get_topic_news(self, topic: str, lang: str = None, max_results: int = 20) -> list[NewsItem]:
        """
        토픽별 뉴스 (Google News 토픽)

        Topics: WORLD, NATION, BUSINESS, TECHNOLOGY, ENTERTAINMENT, SPORTS, SCIENCE, HEALTH
        """
        lang = lang or self.default_lang
        locale = self.LOCALES.get(lang, self.LOCALES["en"])

        topic_url = f"https://news.google.com/rss/topics/{topic}?hl={locale['hl']}&gl={locale['gl']}&ceid={locale['ceid']}"

        try:
            feed = feedparser.parse(topic_url)
        except Exception as e:
            print(f"[GoogleNews] Error fetching topic feed: {e}")
            return []

        news_items = []
        for entry in feed.entries[:max_results]:
            title = entry.get("title", "")
            source = "Unknown"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                if len(parts) == 2:
                    title = parts[0]
                    source = parts[1]

            news_items.append(NewsItem(
                title=title,
                url=entry.get("link", ""),
                source=f"via {source}",
                source_type="news",
                platform="google_news",
                timestamp=entry.get("published", ""),
                content_preview=entry.get("summary", "")[:500] if entry.get("summary") else None
            ))

        return news_items


# 편의 함수
def collect_news_by_keywords(keywords: list[str], lang: str = "en", when: str = "1d") -> list[NewsItem]:
    """키워드 리스트로 뉴스 수집 (간편 함수)"""
    aggregator = GoogleNewsAggregator(default_lang=lang)
    return aggregator.search_multiple(keywords, when=when)


if __name__ == "__main__":
    # 테스트
    aggregator = GoogleNewsAggregator()

    print("=== Google News RSS Test ===\n")

    # 단일 키워드 검색
    print("1. Single keyword search:")
    items = aggregator.search("browser automation AI", when="7d", max_results=5)
    for item in items[:3]:
        print(f"  - {item.title[:60]}...")
        print(f"    Source: {item.source}")
        print()

    # 다중 키워드 검색
    print("2. Multiple keyword search:")
    keywords = ["Browserbase", "AI agent startup", "web scraping"]
    items = aggregator.search_multiple(keywords, when="7d", max_per_keyword=3)
    print(f"   Total unique items: {len(items)}")
