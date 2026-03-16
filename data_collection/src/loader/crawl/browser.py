from __future__ import annotations

from contextlib import asynccontextmanager

from playwright.async_api import async_playwright


@asynccontextmanager
async def create_browser_context(*, headless: bool = True, locale: str = "ko-KR"):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)
        context = await browser.new_context(locale=locale)
        try:
            yield context
        finally:
            await context.close()
            await browser.close()
