"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    tracking_number: str
    tracking_url: str
    keyword: str
    ntfy_topic: str
    ntfy_server: str
    state_file: str
    page_timeout_ms: int

    @classmethod
    def from_env(cls) -> Config:
        tracking_number = os.environ.get("TRACKING_NUMBER", "").strip()
        if not tracking_number:
            raise ValueError("TRACKING_NUMBER environment variable is required.")

        ntfy_topic = os.environ.get("NTFY_TOPIC", "").strip()
        if not ntfy_topic:
            raise ValueError("NTFY_TOPIC environment variable is required.")

        default_url = "https://al.albaniancourier.al/track-trace/"

        return cls(
            tracking_number=tracking_number,
            tracking_url=os.environ.get("TRACKING_URL", default_url).strip(),
            keyword=os.environ.get("KEYWORD", "Vore").strip(),
            ntfy_topic=ntfy_topic,
            ntfy_server=os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/"),
            state_file=os.environ.get("STATE_FILE", ".tracker-state.json"),
            page_timeout_ms=int(os.environ.get("PAGE_TIMEOUT_MS", "90000")),
        )
