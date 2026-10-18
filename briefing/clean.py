"""Turn newsletter and article HTML into plain text worth sending to Claude."""

from __future__ import annotations

import re

import trafilatura

# Lines that are newsletter furniture rather than content. Matched case-insensitively
# against whole lines, so a sentence that merely mentions "subscribe" is kept.
BOILERPLATE_PATTERNS = [
    r"view (this email )?in (your )?browser",
    r"unsubscribe.*",
    r"manage (your )?(preferences|subscription).*",
    r"update (your )?(email )?preferences.*",
    r"you('re| are) receiving this (email )?because.*",
    r"forward(ed)? (this|to a friend).*",
    r"(was this|this email was) forwarded to you\??.*",
    r"sign up (here|now|for free).*",
    r"follow us on .*",
    r"(advertise|sponsor) (with us|this newsletter).*",
    r"copyright ©.*|© \d{4}.*",
    r"privacy policy.*",
    r"\d+ .*(street|st\.|avenue|ave\.|suite).*\d{5}.*",  # postal address footers
]
_BOILERPLATE = re.compile(r"^\s*(" + "|".join(BOILERPLATE_PATTERNS) + r")\s*$", re.IGNORECASE)


def html_to_text(html: str) -> str:
    """Extract readable text from HTML, falling back to tag stripping if extraction finds nothing."""
    text = trafilatura.extract(html, include_comments=False, include_tables=True, favor_recall=True)
    if not text:
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<br\s*/?>|</p>|</div>|</tr>|</h\d>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
    return tidy(text)


def tidy(text: str) -> str:
    """Drop boilerplate lines, collapse whitespace and repeated blank lines."""
    lines = []
    for line in text.splitlines():
        line = re.sub(r"[ \t ‌​]+", " ", line).strip()
        if _BOILERPLATE.match(line):
            continue
        lines.append(line)
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def truncate(text: str, max_chars: int) -> str:
    """Cut long text at a paragraph boundary and say so, so Claude knows it is partial."""
    if len(text) <= max_chars:
        return text
    cut = text.rfind("\n\n", 0, max_chars)
    if cut < max_chars // 2:
        cut = max_chars
    return text[:cut].rstrip() + "\n\n[Truncated]"
