"""Collect recent entries from RSS/Atom feeds, optionally fetching the full article."""

from __future__ import annotations

import calendar
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import feedparser
import httpx

from briefing.clean import html_to_text, truncate
from briefing.models import Item, ItemType, text_hash

USER_AGENT = "daily-briefing/0.1 (personal research digest)"
TIMEOUT = 20


def collect(cfg: dict, max_chars: int, client: httpx.Client | None = None) -> tuple[list[Item], list[str]]:
    """Returns (items, errors). One broken feed is reported, not fatal."""
    client = client or httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT, follow_redirects=True)
    since = datetime.now(timezone.utc) - timedelta(hours=cfg.get("lookback_hours", 36))
    items, errors = [], []
    for feed in cfg.get("feeds", []):
        try:
            response = client.get(feed["url"])
            response.raise_for_status()
            entries = parse_feed(response.content, feed, since, cfg.get("max_items_per_feed", 20))
        except Exception as exc:  # noqa: BLE001 - any failure just skips this feed
            errors.append(f"{feed['name']}: {type(exc).__name__}: {exc}")
            continue
        for item, link in entries:
            if feed.get("fetch_full_text") and link:
                full = fetch_article(client, link)
                if full and len(full) > len(item.clean_text):
                    item.clean_text = full
            item.clean_text = truncate(item.clean_text, max_chars)
            item.content_hash = text_hash(item.clean_text)
            items.append(item)
    return items, errors


def parse_feed(content: bytes, feed: dict, since: datetime, limit: int) -> list[tuple[Item, str | None]]:
    parsed = feedparser.parse(content)
    if parsed.bozo and not parsed.entries:
        raise ValueError(f"not a valid feed ({parsed.bozo_exception})")
    results = []
    for entry in parsed.entries[:limit]:
        published = _entry_time(entry)
        if published and published < since:
            continue
        body = entry.get("content", [{}])[0].get("value") or entry.get("summary", "")
        text = html_to_text(body) if body else ""
        link = entry.get("link")
        results.append(
            (
                Item(
                    source=f"RSS: {feed['name']}",
                    type=ItemType(feed.get("type", "news")),
                    title=entry.get("title", "(untitled)"),
                    url=link,
                    published_at=published or datetime.now(timezone.utc),
                    clean_text=text or entry.get("title", ""),
                    author=entry.get("author"),
                ),
                link,
            )
        )
    return results


def fetch_article(client: httpx.Client, url: str) -> str | None:
    """Fetch an article's text only if the site's robots.txt allows it. Paywalled pages simply yield little text."""
    if not _allowed_by_robots(url):
        return None
    try:
        response = client.get(url)
        response.raise_for_status()
    except httpx.HTTPError:
        return None
    return html_to_text(response.text) or None


@lru_cache(maxsize=64)
def _robots_for(origin: str) -> RobotFileParser:
    parser = RobotFileParser()
    try:
        response = httpx.get(f"{origin}/robots.txt", headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        parser.parse(response.text.splitlines() if response.status_code == 200 else [])
    except httpx.HTTPError:
        parser.parse([])
    return parser


def _allowed_by_robots(url: str) -> bool:
    parts = urlsplit(url)
    return _robots_for(f"{parts.scheme}://{parts.netloc}").can_fetch(USER_AGENT, url)


def _entry_time(entry) -> datetime | None:
    struct = entry.get("published_parsed") or entry.get("updated_parsed")
    if not struct:
        return None
    return datetime.fromtimestamp(calendar.timegm(struct), timezone.utc)
