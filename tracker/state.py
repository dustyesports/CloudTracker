"""Persistent state to avoid duplicate notifications."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TrackerState:
    keyword_found: bool = False
    content_hash: str = ""
    last_snippet: str = ""


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_state(path: str) -> TrackerState:
    state_path = Path(path)
    if not state_path.exists():
        return TrackerState()

    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        return TrackerState(
            keyword_found=bool(data.get("keyword_found", False)),
            content_hash=str(data.get("content_hash", "")),
            last_snippet=str(data.get("last_snippet", "")),
        )
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read state file (%s); starting fresh.", exc)
        return TrackerState()


def save_state(path: str, state: TrackerState) -> None:
    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")


def extract_snippet(text: str, keyword: str, radius: int = 120) -> str:
    index = text.lower().find(keyword.lower())
    if index == -1:
        return text[:240]

    start = max(0, index - radius)
    end = min(len(text), index + len(keyword) + radius)
    snippet = text[start:end].strip()
    if start > 0:
        snippet = f"...{snippet}"
    if end < len(text):
        snippet = f"{snippet}..."
    
    # Limit to tweet length (280 characters)
    if len(snippet) > 280:
        snippet = snippet[:277] + "..."
    
    return snippet
