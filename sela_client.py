"""
Sela API Client for scraping Twitter, LinkedIn, Medium, and websites
Supports keyword-based search across multiple platforms
"""
import requests
import time
import re
from typing import Optional
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from config import SELA_API_BASE_URL, SELA_API_KEY


@dataclass
class NewsItem:
    """Represents a single news item"""
    title: str
    url: str
    source: str
    source_type: str  # "twitter", "linkedin", "medium", "website", "google"
    platform: str = ""  # Platform identifier
    timestamp: Optional[str] = None
    author: Optional[str] = None
    content_preview: Optional[str] = None


class SelaClient:
    """Client for interacting with Sela API - Multi-platform support"""

    def __init__(self, api_key: str = SELA_API_KEY):
        self.api_key = api_key
        self.base_url = SELA_API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # 라운드 로빈 상태 관리
        self._round_robin_index = 0

    def _make_request(self, endpoint: str, payload: dict, timeout: int = 120) -> Optional[dict]:
        """Make a request to the Sela API"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=timeout)
            result = response.json()

            if not result.get("success", False):
                message = result.get("message", "Unknown error")
                if "No available nodes" in message:
                    print(f"[SelaClient] No nodes available, skipping...")
                elif "empty results" in message.lower():
                    pass  # Silent for empty results
                else:
                    print(f"[SelaClient] API error: {message}")
                return None

            return result
        except requests.exceptions.RequestException as e:
            print(f"[SelaClient] Request error: {e}")
            return None

    # =========================================================================
    # Twitter API Methods
    # =========================================================================

    def scrape_twitter_profile(self, username: str, post_count: int = 10) -> list[NewsItem]:
        """Scrape recent tweets from a Twitter profile"""
        payload = {
            "url": f"https://twitter.com/{username}",
            "scrapeType": "TWITTER_PROFILE",
            "timeoutMs": 60000,
            "postCount": post_count,
            "scrollPauseTime": 2000
        }

        result = self._make_request("/api/rpc/scrapeURL", payload)
        if not result or "data" not in result:
            return []

        news_items = []
        data = result.get("data", {})

        # Handle result field (raw data)
        if isinstance(data, dict) and "result" in data:
            result_data = data.get("result")
            if isinstance(result_data, list):
                for tweet in result_data[:post_count]:
                    if isinstance(tweet, dict):
                        text = tweet.get("text", "") or tweet.get("content", "")
                        news_items.append(NewsItem(
                            title=text[:200],
                            url=tweet.get("url", f"https://twitter.com/{username}"),
                            source=f"@{username}",
                            source_type="twitter",
                            platform="twitter",
                            timestamp=tweet.get("created_at") or tweet.get("timestamp"),
                            author=username,
                            content_preview=text[:500]
                        ))
            elif isinstance(result_data, dict):
                tweets = result_data.get("tweets", []) or result_data.get("posts", [])
                for tweet in tweets[:post_count]:
                    if isinstance(tweet, dict):
                        text = tweet.get("text", "") or tweet.get("content", "")
                        news_items.append(NewsItem(
                            title=text[:200],
                            url=tweet.get("url", f"https://twitter.com/{username}"),
                            source=f"@{username}",
                            source_type="twitter",
                            platform="twitter",
                            timestamp=tweet.get("created_at"),
                            author=username,
                            content_preview=text[:500]
                        ))

        return news_items

    def scrape_twitter_post(self, post_url: str, reply_count: int = 5) -> Optional[NewsItem]:
        """Scrape a specific Twitter post"""
        payload = {
            "url": post_url,
            "scrapeType": "TWITTER_POST",
            "timeoutMs": 60000,
            "replyCount": reply_count,
            "scrollPauseTime": 3000
        }

        result = self._make_request("/api/rpc/scrapeURL", payload)
        if not result or "data" not in result:
            return None

        data = result.get("data", {})
        if isinstance(data, dict):
            result_data = data.get("result", data)
            if isinstance(result_data, dict):
                text = result_data.get("text", "") or result_data.get("content", "")
                return NewsItem(
                    title=text[:200],
                    url=post_url,
                    source="Twitter",
                    source_type="twitter",
                    platform="twitter",
                    timestamp=result_data.get("created_at"),
                    author=result_data.get("author", {}).get("username") if isinstance(result_data.get("author"), dict) else None,
                    content_preview=text[:500]
                )
        return None

    # =========================================================================
    # LinkedIn API Methods
    # =========================================================================

    def search_linkedin(self, keywords: str, post_count: int = 10) -> list[NewsItem]:
        """Search LinkedIn posts by keywords"""
        payload = {
            "search_parameters": {
                "keywords": keywords
            },
            "timeoutMs": 120000,
            "postCount": post_count
        }

        result = self._make_request("/api/rpc/linkedInScrape", payload)
        if not result or "data" not in result:
            return []

        news_items = []
        data = result.get("data", {})

        if isinstance(data, dict) and "result" in data:
            result_data = data.get("result")
            posts = result_data if isinstance(result_data, list) else result_data.get("posts", []) if isinstance(result_data, dict) else []

            for post in posts[:post_count]:
                if isinstance(post, dict):
                    text = post.get("text", "") or post.get("content", "") or post.get("title", "")
                    author = post.get("author", {})
                    author_name = author.get("name", "") if isinstance(author, dict) else str(author)

                    news_items.append(NewsItem(
                        title=text[:200],
                        url=post.get("url", post.get("link", "https://linkedin.com")),
                        source=f"LinkedIn: {author_name}" if author_name else "LinkedIn",
                        source_type="linkedin",
                        platform="linkedin",
                        timestamp=post.get("timestamp") or post.get("date"),
                        author=author_name,
                        content_preview=text[:500]
                    ))

        return news_items

    # =========================================================================
    # Medium API Methods
    # =========================================================================

    def search_medium(self, keywords: str) -> list[NewsItem]:
        """Search Medium articles by keywords"""
        payload = {
            "search_parameters": {
                "scrapeType": "MEDIUM_SEARCH",
                "keywords": keywords
            },
            "timeoutMs": 120000
        }

        result = self._make_request("/api/rpc/mediumScrape", payload)
        if not result or "data" not in result:
            return []

        news_items = []
        data = result.get("data", {})

        if isinstance(data, dict) and "result" in data:
            result_data = data.get("result")
            articles = result_data if isinstance(result_data, list) else result_data.get("articles", []) if isinstance(result_data, dict) else []

            for article in articles[:20]:
                if isinstance(article, dict):
                    title = article.get("title", "") or article.get("text", "")[:100]
                    author = article.get("author", {})
                    author_name = author.get("name", "") if isinstance(author, dict) else str(author) if author else ""

                    news_items.append(NewsItem(
                        title=title[:200],
                        url=article.get("url", article.get("link", "https://medium.com")),
                        source=f"Medium: {author_name}" if author_name else "Medium",
                        source_type="medium",
                        platform="medium",
                        timestamp=article.get("publishedAt") or article.get("date"),
                        author=author_name,
                        content_preview=article.get("subtitle", "") or article.get("preview", "")
                    ))

        return news_items

    def scrape_medium_post(self, post_id: str) -> Optional[NewsItem]:
        """Scrape a specific Medium post by ID"""
        payload = {
            "search_parameters": {
                "scrapeType": "MEDIUM_POST",
                "id": post_id
            },
            "timeoutMs": 60000
        }

        result = self._make_request("/api/rpc/mediumScrape", payload)
        if not result or "data" not in result:
            return None

        data = result.get("data", {})
        if isinstance(data, dict) and "result" in data:
            article = data.get("result", {})
            if isinstance(article, dict):
                title = article.get("title", "")
                author = article.get("author", {})
                author_name = author.get("name", "") if isinstance(author, dict) else ""

                return NewsItem(
                    title=title[:200],
                    url=article.get("url", f"https://medium.com/p/{post_id}"),
                    source=f"Medium: {author_name}" if author_name else "Medium",
                    source_type="medium",
                    platform="medium",
                    timestamp=article.get("publishedAt"),
                    author=author_name,
                    content_preview=article.get("content", "")[:500]
                )
        return None

    # =========================================================================
    # HTML/Website Scraping Methods
    # =========================================================================

    def _parse_html_for_news(self, html_content: str, base_url: str, source_name: str) -> list[NewsItem]:
        """Parse HTML content and extract news items"""
        news_items = []
        soup = BeautifulSoup(html_content, 'lxml')

        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        # Strategy 1: Find article headlines
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            link = heading.find('a', href=True)
            if link:
                title = link.get_text(strip=True)
                href = link['href']
                if title and len(title) > 10:
                    full_url = urljoin(base_url, href)
                    if not full_url.startswith('javascript'):
                        news_items.append(NewsItem(
                            title=title[:200],
                            url=full_url,
                            source=source_name,
                            source_type="website",
                            platform="web"
                        ))

        # Strategy 2: Find links within article containers
        containers = soup.find_all(['article', 'div'], class_=re.compile(
            r'story|article|post|item|entry|card|news|headline|titleline', re.I
        ))
        for container in containers:
            link = container.find('a', href=True)
            if link:
                title = link.get_text(strip=True)
                href = link['href']
                if title and len(title) > 15 and not re.match(r'^(home|about|contact|login|sign)', title.lower()):
                    full_url = urljoin(base_url, href)
                    if not full_url.startswith('javascript') and full_url not in [item.url for item in news_items]:
                        news_items.append(NewsItem(
                            title=title[:200],
                            url=full_url,
                            source=source_name,
                            source_type="website",
                            platform="web"
                        ))

        # Strategy 3: Hacker News specific
        if 'ycombinator' in base_url:
            for span in soup.find_all('span', class_='titleline'):
                link = span.find('a', href=True)
                if link:
                    title = link.get_text(strip=True)
                    href = link['href']
                    if title:
                        full_url = href if href.startswith('http') else urljoin(base_url, href)
                        news_items.append(NewsItem(
                            title=title[:200],
                            url=full_url,
                            source=source_name,
                            source_type="website",
                            platform="web"
                        ))

        return news_items[:30]

    def scrape_html(self, url: str, source_name: str) -> list[NewsItem]:
        """Scrape HTML content from a website"""
        payload = {
            "url": url,
            "scrapeType": "HTML",
        }

        result = self._make_request("/api/rpc/scrapeURL", payload)
        if not result or "data" not in result:
            return []

        data = result.get("data", {})

        if isinstance(data, dict) and "result" in data:
            html_content = data.get("result", "")
            if html_content and isinstance(html_content, str):
                return self._parse_html_for_news(html_content, url, source_name)

        return []

    # =========================================================================
    # Google News Scraping Methods (via HTML)
    # =========================================================================

    def scrape_google_news(self, keyword: str, time_range: str = "1d",
                           max_results: int = 20, lang: str = "en",
                           page_delay_sec: float = 5) -> list[NewsItem]:
        """
        Sela API HTML 스크래핑으로 Google News 검색 결과 수집 (최신순, 페이지네이션)

        Args:
            keyword: 검색 키워드
            time_range: 시간 범위 (1h, 1d, 7d, 1m)
            max_results: 최대 결과 수 (페이지네이션으로 50개까지 가능)
            lang: 언어 (en, ko)
            page_delay_sec: 페이지 간 대기 시간

        Returns:
            NewsItem 리스트 (최신순)
        """
        # 시간 범위 매핑 (Google 검색 파라미터)
        time_params = {
            "1h": "qdr:h",   # 지난 1시간
            "1d": "qdr:d",   # 지난 1일
            "7d": "qdr:w",   # 지난 1주
            "1m": "qdr:m",   # 지난 1달
        }

        # 언어/지역 설정
        locale_settings = {
            "en": {"hl": "en", "gl": "us"},
            "ko": {"hl": "ko", "gl": "kr"},
        }
        locale = locale_settings.get(lang, locale_settings["en"])
        time_param = time_params.get(time_range, "qdr:d")
        encoded_keyword = keyword.replace(" ", "+")

        all_items = []
        seen_urls = set()
        per_page = 10  # Google 검색 페이지당 결과 수
        pages_needed = (max_results + per_page - 1) // per_page  # 올림 계산
        pages_needed = min(pages_needed, 5)  # 최대 5페이지 (50개)

        for page in range(pages_needed):
            start = page * per_page

            # Google News 검색 URL 구성 (최신순: sbd:1)
            url = (
                f"https://www.google.com/search?"
                f"q={encoded_keyword}&tbm=nws&tbs=sbd:1,{time_param}"
                f"&hl={locale['hl']}&gl={locale['gl']}&num={per_page}&start={start}"
            )

            payload = {
                "url": url,
                "scrapeType": "HTML",
                "timeoutMs": 60000
            }

            result = self._make_request("/api/rpc/scrapeURL", payload)
            if not result or "data" not in result:
                break  # 실패하면 중단

            data = result.get("data", {})
            html_content = ""

            if isinstance(data, dict) and "result" in data:
                html_content = data.get("result", "")
            elif isinstance(data, str):
                html_content = data

            if not html_content:
                break

            # 페이지 파싱
            page_items = self._parse_google_news_html(html_content, keyword, silent=True)

            # 중복 제거하며 추가
            new_count = 0
            for item in page_items:
                if item.url not in seen_urls:
                    seen_urls.add(item.url)
                    all_items.append(item)
                    new_count += 1

            # 새로운 결과가 없으면 중단 (더 이상 페이지 없음)
            if new_count == 0:
                break

            # 목표 달성하면 중단
            if len(all_items) >= max_results:
                break

            # 다음 페이지 전 대기 (마지막 페이지 제외)
            if page < pages_needed - 1:
                time.sleep(page_delay_sec)

        print(f"  [SelaGoogleNews] '{keyword}': {len(all_items)} items ({pages_needed} pages)")
        return all_items[:max_results]

    def _parse_google_news_html(self, html_content: str, keyword: str, silent: bool = False) -> list[NewsItem]:
        """Google News 검색 결과 HTML 파싱"""
        news_items = []
        soup = BeautifulSoup(html_content, 'lxml')

        # Google News 결과 컨테이너 찾기 (여러 가지 구조 대응)
        # 방법 1: 뉴스 카드 형태
        news_cards = soup.find_all('div', {'class': re.compile(r'SoaBEf|WlydOe|Gx5Zad')})

        for card in news_cards:
            try:
                # 제목과 링크 추출
                title_elem = card.find('div', {'role': 'heading'}) or card.find('h3') or card.find('a')
                link_elem = card.find('a', href=True)

                if not link_elem:
                    continue

                href = link_elem.get('href', '')
                # Google 리다이렉트 URL 처리
                if href.startswith('/url?'):
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(href)
                    params = parse_qs(parsed.query)
                    href = params.get('q', [href])[0]
                elif not href.startswith('http'):
                    continue

                # 제목 추출
                title = ""
                if title_elem:
                    title = title_elem.get_text(strip=True)
                else:
                    title = link_elem.get_text(strip=True)

                if not title or len(title) < 10:
                    continue

                # 소스/출처 추출
                source = "Google News"
                source_elem = card.find('div', {'class': re.compile(r'CEMjEf|NUnG9d')}) or \
                              card.find('span', {'class': re.compile(r'CEMjEf')})
                if source_elem:
                    source = source_elem.get_text(strip=True)

                # 시간 정보 추출
                timestamp = None
                time_elem = card.find('span', {'class': re.compile(r'WG9SHc|r0bn4c|OSrXXb')}) or \
                            card.find('time')
                if time_elem:
                    timestamp = time_elem.get_text(strip=True)

                # 미리보기 텍스트
                preview = ""
                preview_elem = card.find('div', {'class': re.compile(r'GI74Re|Y3v8qd')})
                if preview_elem:
                    preview = preview_elem.get_text(strip=True)

                news_items.append(NewsItem(
                    title=title[:200],
                    url=href,
                    source=f"via {source}",
                    source_type="news",
                    platform="google_news_sela",
                    timestamp=timestamp,
                    content_preview=preview[:500] if preview else None
                ))

            except Exception as e:
                continue

        # 방법 2: 전통적인 검색 결과 형태 (fallback)
        if not news_items:
            for g in soup.find_all('div', class_='g'):
                try:
                    link = g.find('a', href=True)
                    title_elem = g.find('h3')

                    if not link or not title_elem:
                        continue

                    href = link.get('href', '')
                    if not href.startswith('http'):
                        continue

                    title = title_elem.get_text(strip=True)
                    if not title:
                        continue

                    # 출처 추출
                    source = "Google News"
                    cite = g.find('cite')
                    if cite:
                        source = cite.get_text(strip=True)

                    news_items.append(NewsItem(
                        title=title[:200],
                        url=href,
                        source=f"via {source}",
                        source_type="news",
                        platform="google_news_sela",
                        timestamp=None,
                        content_preview=None
                    ))

                except Exception:
                    continue

        if not silent:
            print(f"  [SelaGoogleNews] '{keyword}': {len(news_items)} items")
        return news_items

    def scrape_google_news_multiple(self, keywords: list[str], time_range: str = "1d",
                                     max_per_keyword: int = 10, lang: str = "en",
                                     rate_limit_sec: float = 5, batch_size: int = 4,
                                     batch_delay_sec: float = 30) -> list[NewsItem]:
        """
        여러 키워드로 Google News 검색 (최신순, 배치 처리)

        Args:
            keywords: 키워드 리스트
            time_range: 시간 범위
            max_per_keyword: 키워드당 최대 결과 수
            lang: 언어
            rate_limit_sec: 키워드 간 대기 시간 (캡챠 회피)
            batch_size: 한 번에 처리할 키워드 수
            batch_delay_sec: 배치 간 대기 시간

        Returns:
            통합 NewsItem 리스트 (중복 제거)
        """
        all_news = []
        seen_urls = set()

        # 키워드를 배치로 분할
        batches = [keywords[i:i + batch_size] for i in range(0, len(keywords), batch_size)]
        total_batches = len(batches)

        print(f"[SelaGoogleNews] Searching {len(keywords)} keywords in {total_batches} batches (batch_size={batch_size})...")

        for batch_idx, batch in enumerate(batches):
            print(f"[SelaGoogleNews] Batch {batch_idx + 1}/{total_batches} ({len(batch)} keywords)")

            for keyword in batch:
                try:
                    items = self.scrape_google_news(keyword, time_range, max_per_keyword, lang)

                    # 중복 URL 제거
                    for item in items:
                        if item.url not in seen_urls:
                            seen_urls.add(item.url)
                            all_news.append(item)

                    time.sleep(rate_limit_sec)  # Rate limiting

                except Exception as e:
                    print(f"  [SelaGoogleNews] '{keyword}': Error - {e}")

            # 배치 간 추가 대기 (마지막 배치 제외)
            if batch_idx < total_batches - 1:
                print(f"[SelaGoogleNews] Batch complete. Waiting {batch_delay_sec}s before next batch...")
                time.sleep(batch_delay_sec)

        print(f"[SelaGoogleNews] Total: {len(all_news)} unique items")
        return all_news

    def scrape_google_news_round_robin(self, keywords: list[str], keywords_per_cycle: int = 2,
                                        time_range: str = "1d", max_per_keyword: int = 10,
                                        lang: str = "en", rate_limit_sec: float = 10) -> list[NewsItem]:
        """
        라운드 로빈 방식 Google News 검색 (캡챠 회피)

        매 호출마다 keywords_per_cycle 개의 키워드만 처리하고,
        다음 호출 시 이어서 처리

        Args:
            keywords: 전체 키워드 리스트
            keywords_per_cycle: 한 주기에 처리할 키워드 수
            time_range: 시간 범위
            max_per_keyword: 키워드당 최대 결과 수
            lang: 언어
            rate_limit_sec: 키워드 간 대기 시간

        Returns:
            NewsItem 리스트
        """
        all_news = []
        seen_urls = set()
        total_keywords = len(keywords)

        # 현재 인덱스에서 시작
        start_idx = self._round_robin_index
        end_idx = min(start_idx + keywords_per_cycle, total_keywords)

        # 순환 처리 (끝에 도달하면 처음부터)
        if start_idx >= total_keywords:
            start_idx = 0
            end_idx = min(keywords_per_cycle, total_keywords)

        current_keywords = keywords[start_idx:end_idx]

        print(f"[SelaGoogleNews] Round Robin: keywords {start_idx+1}-{end_idx}/{total_keywords}")
        print(f"[SelaGoogleNews] Processing: {current_keywords}")

        for i, keyword in enumerate(current_keywords):
            try:
                items = self.scrape_google_news(keyword, time_range, max_per_keyword, lang)

                for item in items:
                    if item.url not in seen_urls:
                        seen_urls.add(item.url)
                        all_news.append(item)

                # 마지막 키워드가 아니면 대기
                if i < len(current_keywords) - 1:
                    print(f"[SelaGoogleNews] Waiting {rate_limit_sec}s...")
                    time.sleep(rate_limit_sec)

            except Exception as e:
                print(f"  [SelaGoogleNews] '{keyword}': Error - {e}")

        # 다음 주기를 위해 인덱스 업데이트
        self._round_robin_index = end_idx if end_idx < total_keywords else 0

        print(f"[SelaGoogleNews] Collected: {len(all_news)} items (next start: {self._round_robin_index})")
        return all_news

    # =========================================================================
    # Google Search Methods
    # =========================================================================

    def google_search(self, query: str, num_results: int = 10) -> list[NewsItem]:
        """Perform a Google search and return results"""
        payload = {
            "url": "https://www.google.com/search",
            "scrapeType": "GOOGLE_SEARCH",
            "search_parameters": {
                "engine": "google",
                "q": query,
                "num": num_results
            }
        }

        result = self._make_request("/api/rpc/scrapeURL", payload)
        if not result or "data" not in result:
            return []

        news_items = []
        data = result.get("data", {})

        if isinstance(data, dict) and "result" in data:
            html_content = data.get("result", "")
            if html_content and isinstance(html_content, str):
                soup = BeautifulSoup(html_content, 'lxml')
                for g in soup.find_all('div', class_='g'):
                    link = g.find('a', href=True)
                    title_elem = g.find('h3')
                    if link and title_elem:
                        title = title_elem.get_text(strip=True)
                        href = link['href']
                        if title and href.startswith('http'):
                            news_items.append(NewsItem(
                                title=title[:200],
                                url=href,
                                source=f"Google: {query}",
                                source_type="google",
                                platform="google"
                            ))

        results = data.get("organic_results", []) if isinstance(data, dict) else []
        for item in results:
            if isinstance(item, dict):
                news_items.append(NewsItem(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    source=f"Google: {query}",
                    source_type="google",
                    platform="google",
                    content_preview=item.get("snippet", "")
                ))

        return news_items[:num_results]

    # =========================================================================
    # Unified Collection Method
    # =========================================================================

    def collect_all_news(self,
                         twitter_accounts: list[str] = None,
                         twitter_keywords: list[str] = None,
                         linkedin_keywords: list[str] = None,
                         medium_keywords: list[str] = None,
                         websites: list[dict] = None,
                         google_queries: list[str] = None) -> list[NewsItem]:
        """Collect news from all configured sources"""
        all_news = []

        # Twitter Profiles
        if twitter_accounts:
            print("[SelaClient] Scraping Twitter profiles...")
            for account in twitter_accounts:
                try:
                    items = self.scrape_twitter_profile(account)
                    all_news.extend(items)
                    print(f"  - @{account}: {len(items)} items")
                    time.sleep(2)
                except Exception as e:
                    print(f"  - @{account}: Error - {e}")

        # LinkedIn Search
        if linkedin_keywords:
            print("[SelaClient] Searching LinkedIn...")
            for keyword in linkedin_keywords:
                try:
                    items = self.search_linkedin(keyword)
                    all_news.extend(items)
                    print(f"  - LinkedIn '{keyword}': {len(items)} items")
                    time.sleep(3)
                except Exception as e:
                    print(f"  - LinkedIn '{keyword}': Error - {e}")

        # Medium Search
        if medium_keywords:
            print("[SelaClient] Searching Medium...")
            for keyword in medium_keywords:
                try:
                    items = self.search_medium(keyword)
                    all_news.extend(items)
                    print(f"  - Medium '{keyword}': {len(items)} items")
                    time.sleep(2)
                except Exception as e:
                    print(f"  - Medium '{keyword}': Error - {e}")

        # Website HTML Scraping
        if websites:
            print("[SelaClient] Scraping websites...")
            for site in websites:
                try:
                    items = self.scrape_html(site["url"], site["name"])
                    all_news.extend(items)
                    print(f"  - {site['name']}: {len(items)} items")
                    time.sleep(2)
                except Exception as e:
                    print(f"  - {site['name']}: Error - {e}")

        # Google Search
        if google_queries:
            print("[SelaClient] Running Google searches...")
            for query in google_queries:
                try:
                    items = self.google_search(query)
                    all_news.extend(items)
                    print(f"  - Google '{query}': {len(items)} items")
                    time.sleep(3)
                except Exception as e:
                    print(f"  - Google '{query}': Error - {e}")

        print(f"[SelaClient] Total collected: {len(all_news)} items")
        return all_news


if __name__ == "__main__":
    client = SelaClient()

    print("=== Testing Sela Client ===\n")

    # Test Google News Scraping (최신순)
    print("1. Testing Google News Scraping (by date)...")
    items = client.scrape_google_news("AI agent startup", time_range="1d", max_results=5)
    print(f"   Found {len(items)} items")
    for item in items[:3]:
        print(f"   - {item.title[:60]}...")
        print(f"     Source: {item.source}, Time: {item.timestamp}")
    print()

    # Test Multiple Keywords
    print("2. Testing Multiple Keywords (Google News)...")
    keywords = ["browser automation", "AI agent funding"]
    items = client.scrape_google_news_multiple(keywords, time_range="7d", max_per_keyword=3)
    print(f"   Total unique items: {len(items)}\n")

    # Test HTML scraping
    print("3. Testing Hacker News...")
    items = client.scrape_html("https://news.ycombinator.com/", "Hacker News")
    print(f"   Found {len(items)} items\n")

    # Test LinkedIn (if available)
    print("4. Testing LinkedIn search...")
    items = client.search_linkedin("browser automation")
    print(f"   Found {len(items)} items\n")

    # Test Medium (if available)
    print("5. Testing Medium search...")
    items = client.search_medium("AI agents")
    print(f"   Found {len(items)} items\n")
