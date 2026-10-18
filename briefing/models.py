"""The shapes data takes as it moves through the pipeline."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class ItemType(StrEnum):
    NEWS = "news"
    NEWSLETTER = "newsletter"
    FILING = "filing"
    PRESS_RELEASE = "press_release"
    PODCAST = "podcast"


@dataclass
class Item:
    """One piece of collected source material, normalised across all collectors."""

    source: str  # e.g. "Gmail: Morning Brew", "RSS: DatacenterDynamics"
    type: ItemType
    title: str
    url: str | None
    published_at: datetime
    clean_text: str
    author: str | None = None
    content_hash: str = field(default="")

    def __post_init__(self) -> None:
        if not self.content_hash:
            self.content_hash = text_hash(self.clean_text)


def text_hash(text: str) -> str:
    """Hash of whitespace- and case-normalised text, so trivial reformatting still dedupes."""
    normalised = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.sha256(normalised.encode()).hexdigest()
