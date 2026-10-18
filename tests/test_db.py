from datetime import datetime, timezone

from briefing import db
from briefing.models import Item, ItemType


def make_item(url: str | None, text: str) -> Item:
    return Item(
        source="test",
        type=ItemType.NEWS,
        title="t",
        url=url,
        published_at=datetime(2026, 10, 18, tzinfo=timezone.utc),
        clean_text=text,
    )


def test_dedupes_by_url_and_by_text(tmp_path):
    conn = db.connect(tmp_path / "t.db")
    assert db.insert_item(conn, make_item("https://a", "Deal announced"))
    assert not db.insert_item(conn, make_item("https://a", "Different text"))
    # Same text with different whitespace/case and no URL is still a duplicate.
    assert not db.insert_item(conn, make_item(None, "deal   ANNOUNCED"))
    assert db.insert_item(conn, make_item("https://b", "Another story"))
