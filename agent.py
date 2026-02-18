"""
Market Intelligence Agent - Main entry point
Real-time and digest mode news delivery to Slack
"""
import sys
import signal
import argparse
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from config import POLLING_INTERVAL_MINUTES, DIGEST_HOUR, DIGEST_MINUTE, ENABLE_AI_SUMMARIES, AI_PROVIDER
from sources import (
    # Google News (일반 뉴스)
    GOOGLE_NEWS_KEYWORDS,
    GOOGLE_NEWS_SETTINGS,
    # GDELT (글로벌 뉴스)
    GDELT_KEYWORDS,
    GDELT_COMPETITORS,
    GDELT_SETTINGS,
    # Sela Google News (최신순)
    SELA_GOOGLE_NEWS_SETTINGS,
    SELA_GOOGLE_NEWS_KEYWORDS,
    # Sela API (소셜 플랫폼)
    TWITTER_ACCOUNTS,
    LINKEDIN_KEYWORDS,
    MEDIUM_KEYWORDS,
    PLATFORM_SETTINGS,
)
from sela_client import SelaClient
from news_aggregator import GoogleNewsAggregator
from gdelt_client import GDELTClient
from news_processor import NewsProcessor
from slack_client import SlackNewsClient
from summarizer import NewsSummarizer


class MarketIntelligenceAgent:
    """Main agent for market intelligence gathering and delivery"""

    def __init__(self, mode: str = "realtime"):
        """
        Initialize the agent

        Args:
            mode: "realtime" for instant alerts, "digest" for daily summary
        """
        self.mode = mode
        self.sela_client = SelaClient()
        self.news_aggregator = GoogleNewsAggregator()
        self.gdelt_client = GDELTClient(
            rate_limit_sec=GDELT_SETTINGS.get("rate_limit_sec", 1.0)
        )
        self.news_processor = NewsProcessor()
        self.slack_client = SlackNewsClient()
        self.summarizer = NewsSummarizer(provider=AI_PROVIDER) if ENABLE_AI_SUMMARIES else None
        self.scheduler = BlockingScheduler()
        self.daily_items = []  # Accumulator for digest mode

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        print("\n[Agent] Shutting down...")
        self.scheduler.shutdown(wait=False)
        sys.exit(0)

    def collect_and_process_news(self) -> list:
        """Collect news from Google News + Sela API (hybrid approach)"""
        print(f"\n[Agent] Starting news collection at {datetime.now().isoformat()}")

        all_raw_news = []

        # ========================================
        # 1. Google News RSS (일반 뉴스)
        # ========================================
        if GOOGLE_NEWS_SETTINGS.get("enabled"):
            print("\n[Agent] === Google News (일반 뉴스) ===")
            google_news = self.news_aggregator.search_multiple(
                keywords=GOOGLE_NEWS_KEYWORDS,
                when=GOOGLE_NEWS_SETTINGS.get("time_range", "1d"),
                max_per_keyword=GOOGLE_NEWS_SETTINGS.get("max_per_keyword", 10)
            )
            # Convert to compatible format
            from sela_client import NewsItem as SelaNewsItem
            for item in google_news:
                all_raw_news.append(SelaNewsItem(
                    title=item.title,
                    url=item.url,
                    source=item.source,
                    source_type=item.source_type,
                    platform=item.platform,
                    timestamp=item.timestamp,
                    content_preview=item.content_preview
                ))
            print(f"[Agent] Google News: {len(google_news)} items")

        # ========================================
        # 2. GDELT (글로벌 뉴스)
        # ========================================
        if GDELT_SETTINGS.get("enabled"):
            print("\n[Agent] === GDELT (글로벌 뉴스) ===")
            from sela_client import NewsItem as SelaNewsItem

            # 키워드 기반 검색
            gdelt_news = self.gdelt_client.search_multiple(
                keywords=GDELT_KEYWORDS,
                lang=GDELT_SETTINGS.get("languages", ["en"])[0] if GDELT_SETTINGS.get("languages") else None,
                country=GDELT_SETTINGS.get("countries"),
                timespan=GDELT_SETTINGS.get("time_range", "24h"),
                max_per_keyword=GDELT_SETTINGS.get("max_per_keyword", 15)
            )

            # 경쟁사 뉴스 검색
            for competitor in GDELT_COMPETITORS:
                competitor_news = self.gdelt_client.search_competitor(
                    competitor,
                    timespan="7d",
                    max_results=10
                )
                gdelt_news.extend(competitor_news)
                print(f"  - Competitor '{competitor}': {len(competitor_news)} items")

            # Convert to compatible format
            for item in gdelt_news:
                all_raw_news.append(SelaNewsItem(
                    title=item.title,
                    url=item.url,
                    source=item.source,
                    source_type=item.source_type,
                    platform=item.platform,
                    timestamp=item.timestamp,
                    content_preview=item.content_preview
                ))
            print(f"[Agent] GDELT: {len(gdelt_news)} items")

        # ========================================
        # 3. Sela Google News (최신순 스크래핑)
        # ========================================
        if SELA_GOOGLE_NEWS_SETTINGS.get("enabled") and PLATFORM_SETTINGS.get("sela_google_news", {}).get("enabled"):
            print("\n[Agent] === Sela Google News (최신순) ===")

            mode = SELA_GOOGLE_NEWS_SETTINGS.get("mode", "round_robin")

            if mode == "round_robin":
                # 라운드 로빈 모드: 매 주기마다 일부 키워드만 처리
                sela_google_news = self.sela_client.scrape_google_news_round_robin(
                    keywords=SELA_GOOGLE_NEWS_KEYWORDS,
                    keywords_per_cycle=SELA_GOOGLE_NEWS_SETTINGS.get("keywords_per_cycle", 2),
                    time_range=SELA_GOOGLE_NEWS_SETTINGS.get("time_range", "1d"),
                    max_per_keyword=SELA_GOOGLE_NEWS_SETTINGS.get("max_per_keyword", 10),
                    lang=SELA_GOOGLE_NEWS_SETTINGS.get("lang", "en"),
                    rate_limit_sec=SELA_GOOGLE_NEWS_SETTINGS.get("rate_limit_sec", 10),
                )
            else:
                # 배치 모드: 한 번에 모든 키워드 처리 (배치 분할)
                sela_google_news = self.sela_client.scrape_google_news_multiple(
                    keywords=SELA_GOOGLE_NEWS_KEYWORDS,
                    time_range=SELA_GOOGLE_NEWS_SETTINGS.get("time_range", "1d"),
                    max_per_keyword=SELA_GOOGLE_NEWS_SETTINGS.get("max_per_keyword", 10),
                    lang=SELA_GOOGLE_NEWS_SETTINGS.get("lang", "en"),
                    rate_limit_sec=SELA_GOOGLE_NEWS_SETTINGS.get("rate_limit_sec", 5),
                    batch_size=SELA_GOOGLE_NEWS_SETTINGS.get("batch_size", 4),
                    batch_delay_sec=SELA_GOOGLE_NEWS_SETTINGS.get("batch_delay_sec", 30),
                )

            all_raw_news.extend(sela_google_news)
            print(f"[Agent] Sela Google News: {len(sela_google_news)} items")

        # ========================================
        # 4. Sela API (소셜 플랫폼)
        # ========================================
        print("\n[Agent] === Sela API (소셜 플랫폼) ===")

        twitter_accounts = TWITTER_ACCOUNTS if PLATFORM_SETTINGS.get("twitter", {}).get("enabled") else None
        linkedin_keywords = LINKEDIN_KEYWORDS if PLATFORM_SETTINGS.get("linkedin", {}).get("enabled") else None
        medium_keywords = MEDIUM_KEYWORDS if PLATFORM_SETTINGS.get("medium", {}).get("enabled") else None

        sela_news = self.sela_client.collect_all_news(
            twitter_accounts=twitter_accounts,
            linkedin_keywords=linkedin_keywords,
            medium_keywords=medium_keywords,
        )
        all_raw_news.extend(sela_news)
        print(f"[Agent] Sela API: {len(sela_news)} items")

        # ========================================
        # 5. Process all collected news
        # ========================================
        print(f"\n[Agent] Total raw: {len(all_raw_news)} items")
        processed_news = self.news_processor.process_batch(all_raw_news)

        print(f"[Agent] Processed {len(processed_news)} relevant items")

        # ========================================
        # 6. Generate AI summaries
        # ========================================
        if self.summarizer and processed_news:
            print(f"[Agent] Generating AI summaries for {len(processed_news)} items...")
            for item in processed_news:
                summary = self.summarizer.summarize(item.news_item)
                if summary:
                    item.summary = summary
            print(f"[Agent] Summaries generated: {sum(1 for i in processed_news if i.summary)}")

        return processed_news

    def realtime_job(self):
        """Job for real-time mode: collect, process, and send immediately"""
        try:
            processed_news = self.collect_and_process_news()

            if processed_news:
                # Send critical items immediately, batch the rest
                self.slack_client.send_batch_update(processed_news)
            else:
                print("[Agent] No new items to report")

        except Exception as e:
            print(f"[Agent] Error in realtime job: {e}")

    def digest_collection_job(self):
        """Job for digest mode: collect and accumulate throughout the day"""
        try:
            processed_news = self.collect_and_process_news()
            self.daily_items.extend(processed_news)

            # Still send critical items immediately even in digest mode
            critical_items = [i for i in processed_news if i.is_critical]
            if critical_items:
                print(f"[Agent] Sending {len(critical_items)} critical items immediately")
                for item in critical_items:
                    self.slack_client.send_breaking_news(item)

        except Exception as e:
            print(f"[Agent] Error in digest collection: {e}")

    def digest_delivery_job(self):
        """Job for digest mode: send daily summary"""
        try:
            print(f"[Agent] Sending daily digest with {len(self.daily_items)} items")
            self.slack_client.send_daily_digest(self.daily_items)
            self.daily_items = []  # Reset accumulator

            # Cleanup old database records
            self.news_processor.cleanup()

        except Exception as e:
            print(f"[Agent] Error in digest delivery: {e}")

    def run(self):
        """Start the agent"""
        print("=" * 60)
        print("  Market Intelligence Agent")
        print(f"  Mode: {self.mode}")
        print(f"  Started at: {datetime.now().isoformat()}")
        print("=" * 60)

        # Test Slack connection
        if not self.slack_client.test_connection():
            print("[Agent] ERROR: Cannot connect to Slack. Check your token.")
            return

        # Send startup message
        self.slack_client.send_startup_message()

        if self.mode == "realtime":
            # Real-time mode: poll every N minutes and send immediately
            self.scheduler.add_job(
                self.realtime_job,
                IntervalTrigger(minutes=POLLING_INTERVAL_MINUTES),
                id="realtime_job",
                name="Real-time news collection and delivery"
            )
            print(f"[Agent] Polling every {POLLING_INTERVAL_MINUTES} minutes")

            # Run immediately on start
            self.realtime_job()

        elif self.mode == "digest":
            # Digest mode: collect throughout day, send summary at specified time
            self.scheduler.add_job(
                self.digest_collection_job,
                IntervalTrigger(minutes=POLLING_INTERVAL_MINUTES),
                id="digest_collection_job",
                name="Digest news collection"
            )

            self.scheduler.add_job(
                self.digest_delivery_job,
                CronTrigger(hour=DIGEST_HOUR, minute=DIGEST_MINUTE),
                id="digest_delivery_job",
                name="Daily digest delivery"
            )
            print(f"[Agent] Collecting every {POLLING_INTERVAL_MINUTES} minutes")
            print(f"[Agent] Digest delivery at {DIGEST_HOUR:02d}:{DIGEST_MINUTE:02d}")

            # Run initial collection
            self.digest_collection_job()

        elif self.mode == "both":
            # Both modes: real-time critical alerts + daily digest
            self.scheduler.add_job(
                self.digest_collection_job,
                IntervalTrigger(minutes=POLLING_INTERVAL_MINUTES),
                id="collection_job",
                name="News collection"
            )

            self.scheduler.add_job(
                self.digest_delivery_job,
                CronTrigger(hour=DIGEST_HOUR, minute=DIGEST_MINUTE),
                id="digest_delivery_job",
                name="Daily digest delivery"
            )
            print(f"[Agent] Polling every {POLLING_INTERVAL_MINUTES} minutes")
            print(f"[Agent] Critical alerts: immediate")
            print(f"[Agent] Digest delivery at {DIGEST_HOUR:02d}:{DIGEST_MINUTE:02d}")

            # Run initial collection
            self.digest_collection_job()

        print("[Agent] Starting scheduler...")
        self.scheduler.start()


def main():
    parser = argparse.ArgumentParser(description="Market Intelligence Agent")
    parser.add_argument(
        "--mode",
        choices=["realtime", "digest", "both"],
        default="realtime",
        help="Delivery mode: realtime (immediate), digest (daily summary), or both"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a single collection cycle and exit"
    )

    args = parser.parse_args()

    agent = MarketIntelligenceAgent(mode=args.mode)

    if args.test:
        print("[Agent] Running test collection...")
        processed = agent.collect_and_process_news()
        print(f"\n[Agent] Found {len(processed)} items:")
        for item in processed[:5]:
            print(f"  {'🚨' if item.is_critical else '📰'} {item.news_item.title[:60]}...")
            print(f"      Source: {item.news_item.source}")
            if item.critical_reasons:
                print(f"      Flags: {', '.join(item.critical_reasons)}")
    else:
        agent.run()


if __name__ == "__main__":
    main()
