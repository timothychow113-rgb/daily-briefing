"""Collect newsletters from a Gmail label using the Gmail API (read-only)."""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr, parsedate_to_datetime
from urllib.parse import quote

from briefing.clean import html_to_text, tidy, truncate
from briefing.config import require_env
from briefing.models import Item, ItemType

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_URI = "https://oauth2.googleapis.com/token"


def build_service():
    """Gmail API client authorised with the refresh token produced by scripts/gmail_auth.py."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials(
        token=None,
        refresh_token=require_env("GMAIL_REFRESH_TOKEN"),
        client_id=require_env("GMAIL_CLIENT_ID"),
        client_secret=require_env("GMAIL_CLIENT_SECRET"),
        token_uri=TOKEN_URI,
        scopes=SCOPES,
    )
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def collect(cfg: dict, max_chars: int, service=None) -> list[Item]:
    service = service or build_service()
    since = datetime.now(timezone.utc) - timedelta(hours=cfg.get("lookback_hours", 36))
    # Gmail search has no hour-level "newer_than", but "after:" accepts a Unix timestamp.
    query = f'label:{cfg["label"]} after:{int(since.timestamp())}'

    ids: list[str] = []
    request = service.users().messages().list(userId="me", q=query, maxResults=100)
    while request is not None:
        response = request.execute()
        ids += [m["id"] for m in response.get("messages", [])]
        request = service.users().messages().list_next(request, response)

    items = []
    for msg_id in ids:
        msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
        item = parse_message(msg, account=cfg.get("account"), max_chars=max_chars)
        if item:
            items.append(item)
    return items


def parse_message(msg: dict, account: str | None, max_chars: int) -> Item | None:
    headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
    sender_name, sender_email = parseaddr(headers.get("from", ""))
    html, plain = _find_bodies(msg["payload"])
    text = html_to_text(html) if html else tidy(plain or "")
    if not text:
        return None

    try:
        published = parsedate_to_datetime(headers["date"])
    except (KeyError, TypeError, ValueError):
        published = datetime.fromtimestamp(int(msg["internalDate"]) / 1000, timezone.utc)

    # Link back to the email itself. authuser picks the right account when several are signed in.
    authuser = f"?authuser={quote(account)}" if account else ""
    url = f"https://mail.google.com/mail/{authuser}#all/{msg['id']}"

    return Item(
        source=f"Newsletter: {sender_name or sender_email}",
        type=ItemType.NEWSLETTER,
        title=headers.get("subject", "(no subject)"),
        url=url,
        published_at=published,
        clean_text=truncate(text, max_chars),
        author=sender_name or None,
    )


def _find_bodies(part: dict) -> tuple[str | None, str | None]:
    """Walk a MIME tree and return the first (html, plain-text) bodies found."""
    html = plain = None
    mime = part.get("mimeType", "")
    data = part.get("body", {}).get("data")
    if data and mime == "text/html":
        html = _decode(data)
    elif data and mime == "text/plain":
        plain = _decode(data)
    for sub in part.get("parts", []) or []:
        sub_html, sub_plain = _find_bodies(sub)
        html = html or sub_html
        plain = plain or sub_plain
    return html, plain


def _decode(data: str) -> str:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")
