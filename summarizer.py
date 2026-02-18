"""
News Summarizer - Fetch article content and summarize with AI (Gemini/Claude)
"""
import os
import requests
from bs4 import BeautifulSoup
from typing import Optional
from sela_client import NewsItem

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class NewsSummarizer:
    """Fetch article content and generate AI summaries"""

    def __init__(self, provider: str = "gemini"):
        """
        Initialize summarizer with AI provider

        Args:
            provider: "gemini", "claude", or "both" (gemini primary, claude fallback)
        """
        self.provider = provider.lower()
        self.gemini_client = None
        self.claude_client = None

        # Initialize Gemini
        if self.provider in ["gemini", "both"] and GEMINI_AVAILABLE:
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if google_api_key:
                genai.configure(api_key=google_api_key)
                self.gemini_client = genai.GenerativeModel("gemini-2.0-flash-exp")
                print("[Summarizer] Gemini initialized (FREE)")
            else:
                print("[Summarizer] Warning: GOOGLE_API_KEY not set")

        # Initialize Claude (fallback or primary)
        if self.provider in ["claude", "both"] and ANTHROPIC_AVAILABLE:
            anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            if anthropic_api_key:
                self.claude_client = Anthropic(api_key=anthropic_api_key)
                print("[Summarizer] Claude initialized")
            else:
                print("[Summarizer] Warning: ANTHROPIC_API_KEY not set")

        if not self.gemini_client and not self.claude_client:
            print("[Summarizer] Warning: No AI provider available. Summaries will be disabled.")

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def fetch_article_content(self, url: str, max_chars: int = 5000) -> Optional[str]:
        """
        Fetch and extract main content from article URL

        Args:
            url: Article URL
            max_chars: Maximum characters to extract

        Returns:
            Article text content or None if failed
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()

            # Try common article selectors
            article_selectors = [
                'article',
                '[role="main"]',
                '.article-content',
                '.post-content',
                '.entry-content',
                'main',
            ]

            content = None
            for selector in article_selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(separator='\n', strip=True)
                    break

            # Fallback to body if no article found
            if not content:
                content = soup.body.get_text(separator='\n', strip=True) if soup.body else ""

            # Clean up whitespace
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            content = '\n'.join(lines)

            # Truncate if too long
            if len(content) > max_chars:
                content = content[:max_chars] + "..."

            return content if content else None

        except Exception as e:
            print(f"[Summarizer] Failed to fetch {url}: {e}")
            return None

    def summarize_with_gemini(self, news_item: NewsItem, content: Optional[str] = None) -> Optional[str]:
        """
        Generate AI summary using Google Gemini API (FREE)

        Args:
            news_item: NewsItem to summarize
            content: Optional full article content. If None, will fetch it.

        Returns:
            Summary string or None if failed
        """
        if not self.gemini_client:
            return None

        # Fetch content if not provided
        if not content:
            content = self.fetch_article_content(news_item.url)

        # Fallback to title + preview if content fetch failed
        if not content:
            content = f"{news_item.title}\n\n{news_item.content_preview or ''}"

        # Prepare prompt
        prompt = f"""You are a market intelligence analyst. Summarize this news article in 2-3 concise sentences in Korean.
Focus on:
- Key facts and what happened
- Why it matters for the market/industry
- Any actionable insights

Article Title: {news_item.title}
Source: {news_item.source}

Content:
{content[:3000]}

Provide a brief, professional summary in Korean:"""

        try:
            response = self.gemini_client.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=300,
                )
            )

            summary = response.text.strip()
            print(f"[Summarizer] Gemini summary: {news_item.title[:50]}...")
            return summary

        except Exception as e:
            print(f"[Summarizer] Gemini API error: {e}")
            return None

    def summarize_with_claude(self, news_item: NewsItem, content: Optional[str] = None) -> Optional[str]:
        """
        Generate AI summary using Claude API (Fallback)

        Args:
            news_item: NewsItem to summarize
            content: Optional full article content. If None, will fetch it.

        Returns:
            Summary string or None if failed
        """
        if not self.claude_client:
            return None

        # Fetch content if not provided
        if not content:
            content = self.fetch_article_content(news_item.url)

        # Fallback to title + preview if content fetch failed
        if not content:
            content = f"{news_item.title}\n\n{news_item.content_preview or ''}"

        # Prepare prompt
        prompt = f"""You are a market intelligence analyst. Summarize this news article in 2-3 concise sentences in Korean.
Focus on:
- Key facts and what happened
- Why it matters for the market/industry
- Any actionable insights

Article Title: {news_item.title}
Source: {news_item.source}

Content:
{content[:3000]}

Provide a brief, professional summary in Korean:"""

        try:
            message = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            summary = message.content[0].text.strip()
            print(f"[Summarizer] Claude summary: {news_item.title[:50]}...")
            return summary

        except Exception as e:
            print(f"[Summarizer] Claude API error: {e}")
            return None

    def summarize(self, news_item: NewsItem, content: Optional[str] = None) -> Optional[str]:
        """
        Generate AI summary using configured provider

        Args:
            news_item: NewsItem to summarize
            content: Optional full article content

        Returns:
            Summary string or None if failed
        """
        # Try Gemini first (primary)
        if self.provider in ["gemini", "both"] and self.gemini_client:
            summary = self.summarize_with_gemini(news_item, content)
            if summary:
                return summary

        # Fallback to Claude
        if self.provider in ["claude", "both"] and self.claude_client:
            summary = self.summarize_with_claude(news_item, content)
            if summary:
                return summary

        return None

    def summarize_batch(self, news_items: list[NewsItem], max_concurrent: int = 5) -> dict[str, str]:
        """
        Summarize multiple news items

        Args:
            news_items: List of NewsItems to summarize
            max_concurrent: Maximum concurrent API calls

        Returns:
            Dictionary mapping URL to summary
        """
        summaries = {}

        for item in news_items:
            summary = self.summarize(item)
            if summary:
                summaries[item.url] = summary

        return summaries


if __name__ == "__main__":
    # Test the summarizer
    summarizer = NewsSummarizer(provider="gemini")

    test_item = NewsItem(
        title="OpenAI launches new AI agent platform",
        url="https://techcrunch.com/2024/01/15/openai-agent-platform",
        source="TechCrunch",
        source_type="website",
        platform="google_news",
        content_preview="OpenAI announced a new platform for building autonomous AI agents..."
    )

    print("Testing summarizer...")
    summary = summarizer.summarize(test_item)
    if summary:
        print(f"\nSummary:\n{summary}")
    else:
        print("\nSummarizer not available (API key not set)")
