"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    tracking_numbers: list[str]
    tracking_url: str
    keyword: str
    ntfy_topic: str
    ntfy_server: str
    state_file: str
    page_timeout_ms: int

    @classmethod
    def from_env(cls) -> Config:
        tracking_numbers_str = os.environ.get("TRACKING_NUMBER", "").strip()
        if not tracking_numbers_str:
            raise ValueError("TRACKING_NUMBER environment variable is required.")

        # Support comma-separated tracking numbers
        tracking_numbers = [tn.strip() for tn in tracking_numbers_str.split(",") if tn.strip()]

        return cls(
            tracking_numbers=tracking_numbers,
            tracking_url="https://al.albaniancourier.al/track-trace/?podNr=",
            keyword="Albanian Courier Vore",
            ntfy_topic="cursorAC",
            ntfy_server="https://ntfy.sh",
            state_file=".tracker-state.json",
            page_timeout_ms=90000,
        )
