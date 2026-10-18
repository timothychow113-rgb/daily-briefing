# Daily Briefing

An automated pipeline that collects newsletters, news feeds, filings and (later) podcasts,
then uses Claude to write one synthesized daily briefing across five sections:
Technology/AI/Digital Infrastructure, M&A & Capital Markets, Industry Themes,
Macroeconomics, and a Concept Worth Understanding.

## Status

| Stage | What | State |
|---|---|---|
| 0 | Project skeleton, config, storage | ✅ |
| 1 | Gmail + RSS collection | ⏳ |
| 2 | Claude synthesis → Markdown briefing (MVP) | ⏳ |
| 3 | Weekday schedule on GitHub Actions | ⏳ |
| 4 | Podcasts | ⏳ |
| 5 | Email delivery | ⏳ |

## How it works

```
collect → store & dedupe (SQLite) → Claude: select & group stories
        → Claude: write briefing with [S#] citations → validate citations → briefings/YYYY-MM-DD.md
```

Claude only ever cites source IDs like `[S3]`; code turns those into links, so citations
can't be invented.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env        # then fill in values; .env is git-ignored
python -m briefing check-config
python -m briefing init-db
pytest -q
```

## Where to change things

- **Sources:** `config/sources.yaml`
- **Priorities, sections, length:** `config/profile.yaml`
- **How Claude writes:** `prompts/`

## Secrets

Never commit credentials. Locally they live in `.env`; on GitHub they're repository
Secrets (Settings → Secrets and variables → Actions).
