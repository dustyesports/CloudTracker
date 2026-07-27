"""Send high-priority push notifications via ntfy."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


def send_alert(
    *,
    ntfy_server: str,
    topic: str,
    title: str,
    message: str,
    click_url: str | None = None,
) -> None:
    """Publish an urgent notification to ntfy."""
    url = f"{ntfy_server}/{topic}"
    headers = {
        "Title": title,
        "Priority": "5",
        "Tags": "package,rotating_light",
    }
    if click_url:
        headers["Click"] = click_url

    logger.info("Sending urgent notification to ntfy topic %s", topic)

    response = httpx.post(
        url,
        content=message.encode("utf-8"),
        headers=headers,
        timeout=30.0,
    )
    response.raise_for_status()

    logger.info("Notification sent successfully.")
