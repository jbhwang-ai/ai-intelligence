"""
Slack Client for delivering news to channels
Categorized and well-formatted message delivery
"""
from datetime import datetime
from typing import Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from config import SLACK_BOT_TOKEN, SLACK_CHANNEL
from news_processor import ProcessedNewsItem


class SlackNewsClient:
    """Client for sending news to Slack"""

    # Platform icons
    PLATFORM_ICONS = {
        "twitter": "𝕏",
        "linkedin": "💼",
        "medium": "📝",
        "google_news": "📰",
        "web": "🌐",
        "google": "🔍",
    }

    # Category detection keywords
    CATEGORIES = {
        "🏢 Competitors": ["browserbase", "browserless", "browser-use", "stagehand"],
        "🤖 AI Agents": ["ai agent", "agentic", "langchain", "crewai", "autogen"],
        "🔧 Browser Automation": ["playwright", "puppeteer", "selenium", "headless", "browser automation"],
        "💰 Funding & Investment": ["funding", "raised", "series", "investment", "acquisition"],
        "📊 Market & Trends": ["rpa", "automation market", "enterprise"],
    }

    def __init__(self, token: str = SLACK_BOT_TOKEN, channel: str = SLACK_CHANNEL):
        self.client = WebClient(token=token)
        self.channel = channel

    def _get_platform_icon(self, platform: str) -> str:
        """Get emoji icon for platform"""
        return self.PLATFORM_ICONS.get(platform, "📄")

    def _format_meta_line(self, category: str, source: str, reasons: list) -> str:
        """Format meta line with tags"""
        tags = []
        for r in reasons[:3]:
            tag = r.split(": ")[1] if ": " in r else r
            tags.append(f"`{tag}`")
        tags_str = " ".join(tags) if tags else ""
        return f"{category} • {source} • {tags_str}"

    def _format_tags(self, reasons: list) -> str:
        """Format critical reasons as tags"""
        tags = []
        for r in reasons[:3]:
            tag = r.split(": ")[1] if ": " in r else r
            tags.append(f"`{tag}`")
        return " ".join(tags) if tags else ""

    def _detect_category(self, item: ProcessedNewsItem) -> str:
        """Detect category based on content"""
        text = (item.news_item.title + " " + (item.news_item.content_preview or "")).lower()

        for category, keywords in self.CATEGORIES.items():
            if any(kw in text for kw in keywords):
                return category
        return "📋 Other News"

    def _categorize_items(self, items: list[ProcessedNewsItem]) -> dict:
        """Group items by category"""
        categorized = {}
        for item in items:
            category = self._detect_category(item)
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(item)
        return categorized

    def _group_by_platform(self, items: list[ProcessedNewsItem]) -> dict:
        """Group items by platform"""
        platforms = {}
        for item in items:
            platform = item.news_item.platform or "other"
            if platform not in platforms:
                platforms[platform] = []
            platforms[platform].append(item)
        return platforms

    def _format_compact_item(self, item: ProcessedNewsItem) -> str:
        """Format a single item in compact style"""
        news = item.news_item
        icon = self._get_platform_icon(news.platform)

        # Truncate title
        title = news.title[:80] + "..." if len(news.title) > 80 else news.title

        # Source info
        if news.source_type == "twitter":
            source = f"@{news.author}" if news.author else news.source
        else:
            source = news.source.replace("via ", "")

        # Add summary if available
        summary_text = f"\n     💡 _{item.summary}_" if item.summary else ""

        return f"{icon} *<{news.url}|{title}>*\n     _{source}_{summary_text}"

    def _format_detailed_item(self, item: ProcessedNewsItem) -> list[dict]:
        """Format a single news item with full details"""
        news = item.news_item
        icon = self._get_platform_icon(news.platform)

        blocks = []

        # Title with link
        title = news.title[:120] + "..." if len(news.title) > 120 else news.title

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{icon} *<{news.url}|{title}>*"
            }
        })

        # AI Summary (if available)
        if item.summary:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"💡 _{item.summary}_"
                }
            })

        # Meta info line
        meta_parts = []
        if news.source_type == "twitter" and news.author:
            meta_parts.append(f"@{news.author}")
        else:
            meta_parts.append(news.source.replace("via ", ""))

        if news.timestamp:
            meta_parts.append(news.timestamp[:16] if len(news.timestamp) > 16 else news.timestamp)

        if item.critical_reasons:
            meta_parts.append(self._format_tags(item.critical_reasons[:2]))

        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": " • ".join(meta_parts)}]
        })

        return blocks

    def send_breaking_news(self, item: ProcessedNewsItem) -> bool:
        """Send a single breaking news alert"""
        news = item.news_item
        icon = self._get_platform_icon(news.platform)
        category = self._detect_category(item)

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 Breaking News",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{icon} *<{news.url}|{news.title[:150]}>*"
                }
            },
            {
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": self._format_meta_line(category, news.source, item.critical_reasons)
                }]
            },
            {"type": "divider"}
        ]

        try:
            self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=f"🚨 Breaking: {news.title}",
                unfurl_links=False,
                unfurl_media=False
            )
            print(f"[Slack] Sent breaking news: {news.title[:50]}...")
            return True
        except SlackApiError as e:
            print(f"[Slack] Error sending breaking news: {e.response['error']}")
            return False

    def send_batch_update(self, items: list[ProcessedNewsItem]) -> bool:
        """Send a batch of news items grouped by category"""
        if not items:
            return True

        critical_items = [i for i in items if i.is_critical]
        regular_items = [i for i in items if not i.is_critical]

        # Send critical items as a grouped alert
        if critical_items:
            self._send_critical_batch(critical_items)

        # Send regular items grouped by category
        if regular_items:
            self._send_categorized_update(regular_items)

        return True

    def _send_critical_batch(self, items: list[ProcessedNewsItem]) -> bool:
        """Send critical items as a batch"""
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"🚨 Critical Alerts ({len(items)})", "emoji": True}
            },
            {"type": "divider"}
        ]

        # Group by category
        categorized = self._categorize_items(items)

        for category, cat_items in categorized.items():
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{category}*"}
            })

            for item in cat_items[:15]:  # 카테고리당 최대 15개
                blocks.extend(self._format_detailed_item(item))

            blocks.append({"type": "divider"})

        # Truncate if needed
        blocks = blocks[:48]

        try:
            self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=f"🚨 {len(items)} Critical Alerts",
                unfurl_links=False,
                unfurl_media=False
            )
            print(f"[Slack] Sent {len(items)} critical items")
            return True
        except SlackApiError as e:
            print(f"[Slack] Error: {e.response['error']}")
            return False

    def _send_categorized_update(self, items: list[ProcessedNewsItem]) -> bool:
        """Send regular items grouped by category"""
        categorized = self._categorize_items(items)

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"📊 Market Update ({len(items)} items)", "emoji": True}
            },
            {
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": f"_{datetime.now().strftime('%Y-%m-%d %H:%M')}_"
                }]
            },
            {"type": "divider"}
        ]

        for category, cat_items in categorized.items():
            # Category header
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{category}* ({len(cat_items)})"}
            })

            # Compact list of items
            item_texts = []
            for item in cat_items[:15]:  # 카테고리당 최대 15개
                item_texts.append(self._format_compact_item(item))

            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": "\n\n".join(item_texts)}
            })

            if len(cat_items) > 15:
                blocks.append({
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": f"_+{len(cat_items) - 15} more..._"}]
                })

            blocks.append({"type": "divider"})

        # Truncate if needed
        blocks = blocks[:48]

        try:
            self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=f"📊 Market Update: {len(items)} items",
                unfurl_links=False,
                unfurl_media=False
            )
            print(f"[Slack] Sent categorized update with {len(items)} items")
            return True
        except SlackApiError as e:
            print(f"[Slack] Error: {e.response['error']}")
            return False

    def send_daily_digest(self, items: list[ProcessedNewsItem]) -> bool:
        """Send a daily digest summary organized by category"""
        today = datetime.now().strftime("%Y-%m-%d")

        if not items:
            try:
                self.client.chat_postMessage(
                    channel=self.channel,
                    text=f"📊 *Daily Digest - {today}*\n\nNo significant news items today.",
                    unfurl_links=False,
                    unfurl_media=False
                )
                return True
            except SlackApiError as e:
                print(f"[Slack] Error: {e.response['error']}")
                return False

        critical_items = [i for i in items if i.is_critical]
        regular_items = [i for i in items if not i.is_critical]

        # Group by platform for stats
        platforms = self._group_by_platform(items)
        platform_stats = " | ".join([
            f"{self._get_platform_icon(p)} {len(items)}"
            for p, items in platforms.items()
        ])

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"📊 Daily Digest - {today}", "emoji": True}
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Total:* {len(items)} items | 🚨 {len(critical_items)} critical\n{platform_stats}"
                }
            },
            {"type": "divider"}
        ]

        # Critical section with categories
        if critical_items:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*🚨 Critical News*"}
            })

            categorized = self._categorize_items(critical_items)
            for category, cat_items in categorized.items():
                blocks.append({
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": f"*{category}*"}]
                })
                for item in cat_items[:3]:
                    blocks.extend(self._format_detailed_item(item))

            blocks.append({"type": "divider"})

        # Regular items by category
        if regular_items:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*📰 Today's News*"}
            })

            categorized = self._categorize_items(regular_items)
            for category, cat_items in list(categorized.items())[:4]:
                item_list = "\n".join([
                    f"• {self._get_platform_icon(i.news_item.platform)} <{i.news_item.url}|{i.news_item.title[:60]}...>"
                    for i in cat_items[:4]
                ])
                if len(cat_items) > 4:
                    item_list += f"\n  _+{len(cat_items) - 4} more_"

                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{category}*\n{item_list}"}
                })

        # Truncate if needed
        blocks = blocks[:48]

        try:
            self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks,
                text=f"📊 Daily Digest: {len(items)} items",
                unfurl_links=False,
                unfurl_media=False
            )
            print(f"[Slack] Sent daily digest with {len(items)} items")
            return True
        except SlackApiError as e:
            print(f"[Slack] Error sending digest: {e.response['error']}")
            return False

    def send_startup_message(self) -> bool:
        """Send a startup notification"""
        try:
            self.client.chat_postMessage(
                channel=self.channel,
                text="🤖 *Market Intelligence Agent* is now online and monitoring news sources.\n\n• Real-time alerts for critical news\n• Daily digest at 9:00 AM",
                unfurl_links=False,
                unfurl_media=False
            )
            return True
        except SlackApiError as e:
            print(f"[Slack] Error: {e.response['error']}")
            return False

    def test_connection(self) -> bool:
        """Test the Slack connection"""
        try:
            response = self.client.auth_test()
            print(f"[Slack] Connected as: {response['user']}")
            return True
        except SlackApiError as e:
            print(f"[Slack] Connection error: {e.response['error']}")
            return False


if __name__ == "__main__":
    # Test the client
    client = SlackNewsClient()
    if client.test_connection():
        print("Slack connection successful!")
    else:
        print("Slack connection failed!")
