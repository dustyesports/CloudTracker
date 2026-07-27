"""Main hourly tracking check."""

from __future__ import annotations

import logging
import sys

from tracker.config import Config
from tracker.notify import send_alert
from tracker.scraper import fetch_tracking_text
from tracker.state import TrackerState, content_hash, extract_snippet, load_state, save_state

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def keyword_present(text: str, keyword: str) -> bool:
    return keyword.lower() in text.lower()


def should_notify(previous: TrackerState, found: bool, new_hash: str) -> bool:
    if not found:
        return False

    if not previous.keyword_found:
        return True

    return previous.content_hash != new_hash


def run_check() -> int:
    config = Config.from_env()
    previous = load_state(config.state_file)

    text = fetch_tracking_text(
        tracking_url=config.tracking_url,
        tracking_number=config.tracking_number,
        timeout_ms=config.page_timeout_ms,
    )

    found = keyword_present(text, config.keyword)
    new_hash = content_hash(text)
    snippet = extract_snippet(text, config.keyword)

    logger.info(
        "Keyword '%s' %s on tracking page.",
        config.keyword,
        "FOUND" if found else "not found",
    )

    if should_notify(previous, found, new_hash):
        send_alert(
            ntfy_server=config.ntfy_server,
            topic=config.ntfy_topic,
            title=f"Package update: {config.keyword} detected",
            message=(
                f"Your Albanian Courier shipment ({config.tracking_number}) "
                f"now mentions '{config.keyword}'.\n\n"
                f"Status excerpt:\n{snippet}"
            ),
            click_url=config.tracking_url,
        )
    elif found:
        logger.info("Keyword still present; skipping duplicate notification.")
    else:
        logger.info("Keyword not found; no notification sent.")

    save_state(
        config.state_file,
        TrackerState(
            keyword_found=found,
            content_hash=new_hash,
            last_snippet=snippet,
        ),
    )
    return 0


def main() -> None:
    try:
        raise SystemExit(run_check())
    except Exception:
        logger.exception("Tracking check failed.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
