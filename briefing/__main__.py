"""Command-line entry point: python -m briefing <command>."""

from __future__ import annotations

import argparse

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


def cmd_not_yet(stage: str):
    def run(args: argparse.Namespace) -> None:
        raise SystemExit(f"Not built yet; arrives in {stage}.")

    return run


def main() -> None:
    parser = argparse.ArgumentParser(prog="briefing", description="Daily intelligence briefing")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db", help="Create the SQLite database").set_defaults(func=cmd_init_db)
    sub.add_parser("check-config", help="Validate config files").set_defaults(func=cmd_check_config)
    sub.add_parser("collect", help="Collect sources only").set_defaults(func=cmd_not_yet("Stage 1"))
    sub.add_parser("run", help="Collect, synthesize, write briefing").set_defaults(func=cmd_not_yet("Stage 2"))
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
