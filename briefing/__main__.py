"""Command-line entry point: python -m briefing <command>."""

from __future__ import annotations

import argparse
from collections import Counter

from briefing import db
from briefing.config import load_yaml


def cmd_init_db(args: argparse.Namespace) -> None:
    db.connect()
    print(f"Database ready at {db.DEFAULT_DB_PATH}")


def cmd_check_config(args: argparse.Namespace) -> None:
    sources = load_yaml("sources.yaml")
    profile = load_yaml("profile.yaml")
    enabled = [name for name in ("gmail", "rss", "edgar") if sources.get(name, {}).get("enabled")]
    print(f"Sections: {', '.join(s['title'] for s in profile['sections'])}")
    print(f"Enabled sources: {', '.join(enabled) or 'none yet'}")


def cmd_collect(args: argparse.Namespace) -> None:
    """Run every enabled collector, store new items, and print what was gathered."""
    from briefing.collectors import gmail, rss

    sources = load_yaml("sources.yaml")
    max_chars = sources["limits"]["max_chars_per_item"]
    items, errors = [], []

    if sources["gmail"].get("enabled"):
        try:
            items += gmail.collect(sources["gmail"], max_chars)
        except SystemExit as exc:  # missing credentials
            errors.append(f"Gmail skipped: {exc}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Gmail: {type(exc).__name__}: {exc}")

    if sources["rss"].get("enabled"):
        rss_items, rss_errors = rss.collect(sources["rss"], max_chars)
        items += rss_items
        errors += rss_errors

    conn = db.connect()
    new = [item for item in items if db.insert_item(conn, item)]

    print(f"Collected {len(items)} items, {len(new)} new, {len(items) - len(new)} already seen.\n")
    for source, count in sorted(Counter(i.source for i in new).items()):
        print(f"  {count:3d}  {source}")
    if args.verbose:
        print()
        for item in new:
            print(f"- [{item.source}] {item.title} ({len(item.clean_text):,} chars)")
    if errors:
        print("\nProblems:")
        for error in errors:
            print(f"  ! {error}")


def cmd_check_feeds(args: argparse.Namespace) -> None:
    """Fetch each configured feed once and report whether it works and how much text it gives."""
    from datetime import datetime, timedelta, timezone

    import httpx

    from briefing.collectors import rss

    feeds = load_yaml("sources.yaml")["rss"].get("feeds", [])
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    with httpx.Client(headers={"User-Agent": rss.USER_AGENT}, timeout=rss.TIMEOUT, follow_redirects=True) as client:
        for feed in feeds:
            try:
                response = client.get(feed["url"])
                response.raise_for_status()
                entries = rss.parse_feed(response.content, feed, week_ago, limit=50)
            except Exception as exc:  # noqa: BLE001
                print(f"FAIL  {feed['name']}: {type(exc).__name__}: {exc}")
                continue
            avg = sum(len(i.clean_text) for i, _ in entries) // max(len(entries), 1)
            line = f"OK    {feed['name']}: {len(entries)} entries in last 7 days, avg {avg:,} chars of text"
            if feed.get("fetch_full_text") and entries and entries[0][1]:
                full = rss.fetch_article(client, entries[0][1])
                line += f"; full article: {len(full):,} chars" if full else "; full article: not available"
            print(line)


def cmd_not_yet(stage: str):
    def run(args: argparse.Namespace) -> None:
        raise SystemExit(f"Not built yet; arrives in {stage}.")

    return run


def main() -> None:
    parser = argparse.ArgumentParser(prog="briefing", description="Daily intelligence briefing")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db", help="Create the SQLite database").set_defaults(func=cmd_init_db)
    sub.add_parser("check-config", help="Validate config files").set_defaults(func=cmd_check_config)
    sub.add_parser("check-feeds", help="Test every RSS feed in config").set_defaults(func=cmd_check_feeds)
    collect = sub.add_parser("collect", help="Collect sources only")
    collect.add_argument("-v", "--verbose", action="store_true", help="List every new item")
    collect.set_defaults(func=cmd_collect)
    sub.add_parser("run", help="Collect, synthesize, write briefing").set_defaults(func=cmd_not_yet("Stage 2"))
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
