"""Fetch Albanian Courier tracking page content with Playwright."""

from __future__ import annotations

import logging
import re

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

BOT_CHALLENGE_MARKERS = (
    "one moment, please",
    "just a moment",
    "checking your browser",
)

TRACKING_INPUT_SELECTORS = (
    'input[name="podNr"]',
    'input[name="tracking"]',
    'input[name="trackingNumber"]',
    'input[id*="track" i]',
    'input[placeholder*="track" i]',
    'input[type="text"]',
)

SUBMIT_SELECTORS = (
    'button[type="submit"]',
    'input[type="submit"]',
    'button:has-text("Track")',
    'button:has-text("Gjurmo")',
    'button:has-text("Search")',
)


def _collect_visible_text(page) -> str:
    """Gather text from the main page and any embedded frames."""
    chunks: list[str] = []

    try:
        chunks.append(page.inner_text("body"))
    except Exception:
        pass

    for frame in page.frames:
        if frame is page.main_frame:
            continue
        try:
            chunks.append(frame.inner_text("body"))
        except Exception:
            continue

    combined = "\n".join(chunk for chunk in chunks if chunk.strip())
    return re.sub(r"\s+", " ", combined).strip()


def _wait_for_real_page(page, timeout_ms: int) -> None:
    """Wait until bot-protection interstitials finish."""
    page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)

    for _ in range(30):
        title = (page.title() or "").lower()
        body_preview = ""
        try:
            body_preview = (page.inner_text("body") or "")[:500].lower()
        except Exception:
            pass

        if not any(marker in title or marker in body_preview for marker in BOT_CHALLENGE_MARKERS):
            return

        page.wait_for_timeout(2000)

    logger.warning("Bot challenge may still be active; continuing with current page content.")


def _maybe_submit_tracking_form(page, tracking_number: str, timeout_ms: int) -> None:
    """Fill and submit a tracking form when the page does not already include the POD."""
    if tracking_number.lower() in (page.content() or "").lower():
        return

    for selector in TRACKING_INPUT_SELECTORS:
        locator = page.locator(selector).first
        if locator.count() == 0:
            continue

        try:
            locator.wait_for(state="visible", timeout=5000)
            locator.fill(tracking_number)

            for submit_selector in SUBMIT_SELECTORS:
                submit = page.locator(submit_selector).first
                if submit.count() == 0:
                    continue
                submit.click()
                page.wait_for_load_state("networkidle", timeout=timeout_ms)
                return

            locator.press("Enter")
            page.wait_for_load_state("networkidle", timeout=timeout_ms)
            return
        except Exception:
            continue


def fetch_tracking_text(tracking_url: str, tracking_number: str, timeout_ms: int) -> str:
    """Load the tracking page in headless Chromium and return visible text."""
    # Append tracking number to URL if URL ends with parameter placeholder
    if tracking_url.endswith("=") and tracking_number:
        tracking_url = f"{tracking_url}{tracking_number}"
    elif "podNr=" not in tracking_url and tracking_number:
        if "?" in tracking_url:
            tracking_url = f"{tracking_url}&podNr={tracking_number}"
        else:
            tracking_url = f"{tracking_url}?podNr={tracking_number}"
    
    logger.info("Fetching tracking page: %s", tracking_url)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            viewport={"width": 1366, "height": 900},
        )
        page = context.new_page()

        try:
            page.goto(tracking_url, wait_until="domcontentloaded", timeout=timeout_ms)
            _wait_for_real_page(page, timeout_ms)
            _maybe_submit_tracking_form(page, tracking_number, timeout_ms)
            page.wait_for_timeout(3000)
            text = _collect_visible_text(page)
        except PlaywrightTimeoutError as exc:
            raise RuntimeError(f"Timed out loading tracking page: {tracking_url}") from exc
        finally:
            browser.close()

    if not text:
        raise RuntimeError("Tracking page loaded but returned no readable text.")

    logger.info("Collected %d characters of tracking text.", len(text))
    return text
