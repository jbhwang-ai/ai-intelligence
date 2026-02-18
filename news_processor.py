"""
News Processor - Deduplication, Critical Flagging, Relevance Filtering
"""
import sqlite3
import hashlib
import re
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field

from sela_client import NewsItem
from config import DB_PATH
from keywords import (
    MUST_HAVE_KEYWORDS,
    INTEREST_KEYWORDS,
    EXCLUDE_KEYWORDS,
    HIGH_AUTHORITY_DOMAINS,
    HIGH_AUTHORITY_TWITTER,
)
from scoring import (
    MUST_HAVE_SCORE,
    INTEREST_SCORE,
    AUTHORITY_SCORE,
    MAX_SCORE,
    RELEVANCE_THRESHOLD,
    CRITICAL_MUST_HAVE_COUNT,
    CRITICAL_MULTI_SOURCE_COUNT,
    MUST_HAVE_SCORE_CAP,
    INTEREST_SCORE_CAP,
    URGENCY_PLUS_AUTHORITY_IS_CRITICAL,
    AUTHORITY_ALONE_IS_RELEVANT,
)


@dataclass
class ProcessedNewsItem:
    """News item with processing metadata"""
    news_item: NewsItem
    is_critical: bool
    is_verified: bool
    is_relevant: bool
    relevance_score: int
    critical_reasons: list[str]
    hash_id: str
    similar_count: int = 0
    matched_keywords: list[str] = field(default_factory=list)
    summary: Optional[str] = None  # AI-generated summary


class NewsDatabase:
    """SQLite database for tracking seen news and deduplication"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seen_news (
                hash_id TEXT PRIMARY KEY,
                title TEXT,
                url TEXT,
                source TEXT,
                source_type TEXT,
                is_critical INTEGER,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                times_seen INTEGER DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_hash TEXT,
                title TEXT,
                source TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_seen_news_hash ON seen_news(hash_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_news_topics_hash ON news_topics(topic_hash)
        """)

        conn.commit()
        conn.close()

    def _generate_hash(self, item: NewsItem) -> str:
        """Generate a hash for deduplication"""
        normalized_title = re.sub(r'[^\w\s]', '', item.title.lower())
        normalized_title = ' '.join(normalized_title.split())
        content = f"{normalized_title}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _generate_topic_hash(self, title: str) -> str:
        """Generate a topic hash for cross-checking similar stories"""
        words = re.sub(r'[^\w\s]', '', title.lower()).split()
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or'}
        key_words = sorted([w for w in words if w not in stopwords and len(w) > 3])[:5]
        return hashlib.md5(' '.join(key_words).encode()).hexdigest()[:12]

    def is_seen(self, item: NewsItem) -> bool:
        """Check if a news item has been seen before"""
        hash_id = self._generate_hash(item)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT hash_id FROM seen_news WHERE hash_id = ?", (hash_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def mark_seen(self, item: NewsItem, is_critical: bool) -> str:
        """Mark a news item as seen and return its hash"""
        hash_id = self._generate_hash(item)
        topic_hash = self._generate_topic_hash(item.title)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO seen_news (hash_id, title, url, source, source_type, is_critical)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(hash_id) DO UPDATE SET times_seen = times_seen + 1
        """, (hash_id, item.title, item.url, item.source, item.source_type, int(is_critical)))

        cursor.execute("""
            INSERT INTO news_topics (topic_hash, title, source)
            VALUES (?, ?, ?)
        """, (topic_hash, item.title, item.source))

        conn.commit()
        conn.close()
        return hash_id

    def get_similar_count(self, item: NewsItem, hours: int = 1) -> int:
        """Get count of similar topics from different sources in the past N hours"""
        topic_hash = self._generate_topic_hash(item.title)
        cutoff = datetime.now() - timedelta(hours=hours)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT source) FROM news_topics
            WHERE topic_hash = ? AND timestamp > ?
        """, (topic_hash, cutoff.isoformat()))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

    def cleanup_old_records(self, days: int = 7):
        """Remove records older than N days"""
        cutoff = datetime.now() - timedelta(days=days)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM seen_news WHERE first_seen < ?", (cutoff.isoformat(),))
        cursor.execute("DELETE FROM news_topics WHERE timestamp < ?", (cutoff.isoformat(),))
        conn.commit()
        conn.close()


class NewsProcessor:
    """Process news items: deduplication, relevance filtering, flagging"""

    def __init__(self):
        self.db = NewsDatabase()

    def _should_exclude(self, item: NewsItem) -> bool:
        """Check if item should be excluded based on EXCLUDE_KEYWORDS"""
        text_to_check = f"{item.title} {item.content_preview or ''}".lower()
        for keyword in EXCLUDE_KEYWORDS:
            if keyword.lower() in text_to_check:
                return True
        return False

    def _check_must_have_keywords(self, item: NewsItem) -> list[str]:
        """Check for must-have keywords (Critical)"""
        matched = []
        text_to_check = f"{item.title} {item.content_preview or ''}".lower()
        for keyword in MUST_HAVE_KEYWORDS:
            if keyword.lower() in text_to_check:
                matched.append(keyword)
        return matched

    def _check_interest_keywords(self, item: NewsItem) -> list[str]:
        """Check for interest keywords"""
        matched = []
        text_to_check = f"{item.title} {item.content_preview or ''}".lower()
        for keyword in INTEREST_KEYWORDS:
            if keyword.lower() in text_to_check:
                matched.append(keyword)
        return matched

    def _check_authority_source(self, item: NewsItem) -> Optional[str]:
        """Check if the source is high authority"""
        for authority in HIGH_AUTHORITY_DOMAINS:
            if authority in item.url.lower():
                return f"Trusted: {authority}"

        if item.source_type == "twitter" and item.author:
            if item.author.lower() in [a.lower() for a in HIGH_AUTHORITY_TWITTER]:
                return f"Trusted: @{item.author}"

        return None

    def _check_urgency_signals(self, item: NewsItem) -> Optional[str]:
        """Check for urgency signals in the title"""
        urgency_patterns = [
            r'\bbreaking\b',
            r'\bjust in\b',
            r'\burgent\b',
            r'\b속보\b',
            r'\b긴급\b',
            r'\bexclusive\b',
            r'\b🚨\b',
            r'\b⚠️\b',
        ]

        title_lower = item.title.lower()
        for pattern in urgency_patterns:
            if re.search(pattern, title_lower, re.IGNORECASE):
                return "🚨 Urgency signal"

        return None

    def _calculate_relevance_score(self, must_have: list, interest: list, authority: bool) -> int:
        """Calculate relevance score using configurable settings from scoring.py"""
        score = 0
        # Must-have keywords
        score += min(len(must_have) * MUST_HAVE_SCORE, MUST_HAVE_SCORE_CAP)
        # Interest keywords
        score += min(len(interest) * INTEREST_SCORE, INTEREST_SCORE_CAP)
        # Authority source
        if authority:
            score += AUTHORITY_SCORE
        return min(score, MAX_SCORE)

    def process_item(self, item: NewsItem) -> Optional[ProcessedNewsItem]:
        """Process a single news item"""
        # Skip if already seen
        if self.db.is_seen(item):
            return None

        # Skip empty or invalid items
        if not item.title or len(item.title.strip()) < 10:
            return None

        # Skip if contains exclude keywords
        if self._should_exclude(item):
            return None

        # Check keywords
        must_have_matches = self._check_must_have_keywords(item)
        interest_matches = self._check_interest_keywords(item)
        all_matched_keywords = must_have_matches + interest_matches

        # Check authority
        authority_reason = self._check_authority_source(item)

        # Check urgency
        urgency_reason = self._check_urgency_signals(item)

        # Check cross-source verification
        similar_count = self.db.get_similar_count(item)
        is_verified = similar_count >= 2

        # Calculate relevance score
        relevance_score = self._calculate_relevance_score(
            must_have_matches,
            interest_matches,
            authority_reason is not None
        )

        # Determine relevance using configurable threshold
        is_relevant = (
            relevance_score >= RELEVANCE_THRESHOLD or
            (AUTHORITY_ALONE_IS_RELEVANT and authority_reason is not None)
        )

        # Build critical reasons
        critical_reasons = []
        if must_have_matches:
            critical_reasons.append(f"Keywords: {', '.join(must_have_matches[:3])}")
        if authority_reason:
            critical_reasons.append(authority_reason)
        if urgency_reason:
            critical_reasons.append(urgency_reason)
        if similar_count >= CRITICAL_MULTI_SOURCE_COUNT:
            critical_reasons.append(f"Multi-source ({similar_count})")

        # Determine if critical using configurable criteria
        is_critical = (
            len(must_have_matches) >= CRITICAL_MUST_HAVE_COUNT or
            (URGENCY_PLUS_AUTHORITY_IS_CRITICAL and urgency_reason is not None and authority_reason is not None) or
            similar_count >= CRITICAL_MULTI_SOURCE_COUNT
        )

        # Mark as seen
        hash_id = self.db.mark_seen(item, is_critical)

        return ProcessedNewsItem(
            news_item=item,
            is_critical=is_critical,
            is_verified=is_verified,
            is_relevant=is_relevant,
            relevance_score=relevance_score,
            critical_reasons=critical_reasons,
            hash_id=hash_id,
            similar_count=similar_count,
            matched_keywords=all_matched_keywords
        )

    def process_batch(self, items: list[NewsItem]) -> list[ProcessedNewsItem]:
        """Process a batch of news items, returning only relevant ones"""
        processed = []
        for item in items:
            result = self.process_item(item)
            # Only include relevant items
            if result and result.is_relevant:
                processed.append(result)

        # Sort: critical first, then by relevance score
        processed.sort(key=lambda x: (not x.is_critical, -x.relevance_score))

        return processed

    def cleanup(self):
        """Perform database cleanup"""
        self.db.cleanup_old_records()


if __name__ == "__main__":
    # Test the processor
    processor = NewsProcessor()

    test_cases = [
        NewsItem(
            title="Browserbase raises $10M Series A for AI browser automation",
            url="https://techcrunch.com/browserbase",
            source="TechCrunch",
            source_type="website"
        ),
        NewsItem(
            title="New iPhone 16 features leaked ahead of launch",
            url="https://theverge.com/iphone",
            source="The Verge",
            source_type="website"
        ),
        NewsItem(
            title="LangChain announces new agent framework update",
            url="https://blog.langchain.dev/update",
            source="LangChain Blog",
            source_type="website"
        ),
    ]

    print("Testing relevance filtering:\n")
    for item in test_cases:
        result = processor.process_item(item)
        if result:
            status = "🚨 CRITICAL" if result.is_critical else ("✅ RELEVANT" if result.is_relevant else "📰 Normal")
            print(f"{status} | Score: {result.relevance_score}")
            print(f"  Title: {item.title[:50]}...")
            print(f"  Keywords: {result.matched_keywords}")
            print(f"  Reasons: {result.critical_reasons}")
            print()
        else:
            print(f"❌ FILTERED OUT: {item.title[:50]}...")
            print()
