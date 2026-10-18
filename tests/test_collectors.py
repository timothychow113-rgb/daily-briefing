import base64
from datetime import datetime, timezone
from pathlib import Path

from briefing.collectors import gmail, rss
from briefing.models import ItemType

FIXTURES = Path(__file__).parent / "fixtures"


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")


def test_gmail_message_prefers_html_part_and_links_back():
    msg = {
        "id": "abc123",
        "internalDate": "1792245600000",
        "payload": {
            "mimeType": "multipart/alternative",
            "headers": [
                {"name": "From", "value": "The Deal Sheet <news@example.com>"},
                {"name": "Subject", "value": "Acme sold for $12.4bn"},
                {"name": "Date", "value": "Sat, 17 Oct 2026 11:00:00 +0000"},
            ],
            "parts": [
                {"mimeType": "text/plain", "body": {"data": _b64("plain version")}},
                {"mimeType": "text/html", "body": {"data": _b64((FIXTURES / "newsletter.html").read_text())}},
            ],
        },
    }
    item = gmail.parse_message(msg, account="tchow29@amherst.edu", max_chars=20000)
    assert item.source == "Newsletter: The Deal Sheet"
    assert item.type is ItemType.NEWSLETTER
    assert item.title == "Acme sold for $12.4bn"
    assert "24x forward EBITDA" in item.clean_text
    assert item.url == "https://mail.google.com/mail/?authuser=tchow29%40amherst.edu#all/abc123"
    assert item.published_at == datetime(2026, 10, 17, 11, tzinfo=timezone.utc)


def test_rss_skips_old_entries():
    feed = {"name": "Example Trade Press", "type": "news"}
    since = datetime(2026, 10, 16, tzinfo=timezone.utc)
    entries = rss.parse_feed((FIXTURES / "feed.xml").read_bytes(), feed, since, limit=20)
    assert [item.title for item, _ in entries] == ["Utility signs 1 GW PPA with hyperscaler"]
    item, link = entries[0]
    assert link == "https://example.com/ppa"
    assert "20-year power purchase agreement" in item.clean_text
