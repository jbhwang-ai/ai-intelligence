# AI Intelligence - Quick Start

## Current Status

✅ **Completed**
- Full agent code structure
- Sela API client implementation
- News processor (deduplication, critical flagging)
- Slack client (realtime alerts + digest)
- Scheduler and main agent logic
- Dependencies installed

## How to Run

### 1. Set Environment Variables

```bash
cp .env.example .env
# Edit .env with your credentials:
# - SELA_API_KEY (required)
# - SLACK_BOT_TOKEN (required)
# - ANTHROPIC_API_KEY or GOOGLE_API_KEY (for AI summaries)
```

### 2. Run Modes

```bash
# Test run (single collection, then exit)
python3 agent.py --test

# Realtime mode (collect every 5 min, instant alerts)
python3 agent.py --mode realtime

# Digest mode (collect all day, send summary at 9 AM)
python3 agent.py --mode digest

# Hybrid mode (critical alerts instantly + daily digest)
python3 agent.py --mode both
```

### 3. Run in Background

```bash
# Run in background with nohup
nohup python3 agent.py --mode both > agent.log 2>&1 &

# Check logs
tail -f agent.log

# Stop the process
ps aux | grep agent.py
kill <PID>
```

## Customization

### config.py Key Settings

```python
# Collection interval (minutes)
POLLING_INTERVAL_MINUTES = 5

# Digest delivery time
DIGEST_HOUR = 9   # 9 AM
DIGEST_MINUTE = 0

# Add critical keywords
CRITICAL_KEYWORDS = [
    "breaking", "urgent",
    "acquisition", "funding", "ipo",
    # add more here...
]
```

### sources.py - Adding Sources

```python
# Add Twitter accounts
TWITTER_ACCOUNTS = [
    "browserbasehq",
    "your_account",  # add here
]

# Add websites
NEWS_WEBSITES = [
    {
        "name": "Your Site",
        "url": "https://example.com",
        "selector": "article h2 a"
    }
]

# Add Google search queries
GOOGLE_SEARCH_QUERIES = [
    "your search query",
]
```

## Slack Setup

1. Create a `#market-intelligence` channel in your Slack workspace
2. Create a Slack App and issue a Bot Token
3. Required scopes: `chat:write`, `chat:write.public`
4. Invite the bot to the channel: `/invite @your-bot-name`

## Troubleshooting

### Twitter scraping returns empty results

**Cause:** Sela API returning empty results or no available nodes

**Fix:**
1. Check Sela API status
2. Verify your Sela API credentials in `.env`
3. Ensure the Twitter account is public
4. Increase rate limiting delay

### Slack message delivery fails

**Cause:** Invalid token or insufficient permissions

**Fix:**
1. Test connection: `python3 slack_client.py`
2. Re-check Bot Token
3. Confirm bot has been invited to the channel

### Duplicate news keeps being sent

**Cause:** Database reset or hash collision

**Fix:**
1. Check `news_cache.db`
2. Clean database: `processor.cleanup()`
3. Adjust hashing logic in `news_processor.py`

## Next Steps

1. **Verify test results**: Check output from `--test` run
2. **Check Slack channel**: Confirm messages are delivered correctly
3. **Start realtime mode**: `python3 agent.py --mode both`
4. **Monitor**: Watch log files and tune performance

## Performance Tips

- **Adjust interval**: 5 min → 10 min to reduce API load
- **Limit sources**: Too many sources increases response time
- **Clean database**: Periodically delete old records
- **Rate limiting**: Increase wait time between API calls

## References

- [Slack API Docs](https://api.slack.com/docs)
- [APScheduler Docs](https://apscheduler.readthedocs.io/)
