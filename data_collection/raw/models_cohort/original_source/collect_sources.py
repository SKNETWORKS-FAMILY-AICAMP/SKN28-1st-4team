from __future__ import annotations

import csv
import json
import logging
import re
import time
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from playwright.sync_api import BrowserContext, Locator, Page, sync_playwright

from source_registry import DOMESTIC_SOURCE_REGISTRY, SourceRegistryEntry, default_registry_rows


LOGGER = logging.getLogger(__name__)
RETRYABLE_FETCH_ERRORS = (URLError, TimeoutError, OSError)


@dataclass(slots=True)
class ModelIndexRow:
    source_id: str
    source_kind: str
    brand: str
    model_name: str
    model_code: str
    category: str
    landing_url: str
    model_url: str
    source_status: str
    notes: str
    collected_at: str


@dataclass(slots=True)
class PriceSourceRow:
    source_id: str
    source_kind: str
    brand: str
    model_name: str
    model_code: str
    category: str
    level_name: str
    level_code: str
    class_name: str
    class_code: str
    year_code: str
    year_label: str
    price_url: str
    catalog_url: str
    landing_url: str
    effective_text: str
    source_status: str
    notes: str
    collected_at: str


@dataclass(slots=True)
class CrawlAuditRow:
    brand: str
    stage: str
    status: str
    detail: str
    collected_at: str


Collector = Callable[..., tuple[list[ModelIndexRow], list[PriceSourceRow], list[CrawlAuditRow]]]


KIA_TABS = ("EV", "PBV", "승용", "RV", "택시 & 상용")
CHEVROLET_MODELS = (
    ("트레일블레이저", "SUV"),
    ("트랙스 크로스오버", "CUV"),
    ("콜로라도", "Trucks"),
)


def collect_all(
    output_dir: Path,
    *,
    include_archive_price_index: bool = False,
    archive_price_model_limit_per_brand: int | None = None,
) -> tuple[list[ModelIndexRow], list[PriceSourceRow], list[CrawlAuditRow]]:
    models: list[ModelIndexRow] = []
    prices: list[PriceSourceRow] = []
    audits: list[CrawlAuditRow] = []

    output_dir.mkdir(parents=True, exist_ok=True)
    write_rows(output_dir / "source_registry.csv", default_registry_rows())

    collectors: dict[str, Collector] = {
        "hyundai": collect_hyundai,
        "kia": collect_kia,
        "chevrolet": collect_chevrolet,
        "renault": collect_renault,
        "kgm": collect_kgm,
        "bobaedream_archive": collect_bobaedream_archive,
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(locale="ko-KR", accept_downloads=True)
        try:
            for entry in DOMESTIC_SOURCE_REGISTRY:
                if not entry.active:
                    continue
                collected_at = now_iso()
                collector = collectors[entry.collector_key]
                LOGGER.info(
                    "Collecting source index: brand=%s source_id=%s source_kind=%s",
                    entry.brand,
                    entry.source_id,
                    entry.source_kind,
                )
                try:
                    if entry.collector_key == "bobaedream_archive":
                        entry_models, entry_prices, entry_audits = collect_bobaedream_archive(
                            context,
                            entry,
                            collected_at,
                            include_price_index=include_archive_price_index,
                            price_model_limit=archive_price_model_limit_per_brand,
                        )
                    else:
                        entry_models, entry_prices, entry_audits = collector(context, entry, collected_at)
                except Exception as exc:  # pragma: no cover - network/runtime safety
                    entry_models = []
                    entry_prices = []
                    entry_audits = [
                        CrawlAuditRow(
                            brand=entry.brand,
                            stage="collect",
                            status="error",
                            detail=f"{type(exc).__name__}: {exc}",
                            collected_at=collected_at,
                        )
                    ]
                models.extend(entry_models)
                prices.extend(entry_prices)
                audits.extend(entry_audits)
                LOGGER.info(
                    "Finished source index: brand=%s source_id=%s model_rows=%s price_rows=%s",
                    entry.brand,
                    entry.source_id,
                    len(entry_models),
                    len(entry_prices),
                )
        finally:
            context.close()
            browser.close()

    write_rows(output_dir / "model_index.csv", [asdict(row) for row in models])
    write_rows(output_dir / "price_source_index.csv", [asdict(row) for row in prices])
    write_rows(output_dir / "crawl_audit.csv", [asdict(row) for row in audits])
    return models, prices, audits


def build_model_row(
    entry: SourceRegistryEntry,
    *,
    model_name: str,
    model_code: str,
    category: str,
    landing_url: str,
    model_url: str,
    source_status: str,
    notes: str,
    collected_at: str,
) -> ModelIndexRow:
    return ModelIndexRow(
        source_id=entry.source_id,
        source_kind=entry.source_kind,
        brand=entry.brand,
        model_name=model_name,
        model_code=model_code,
        category=category,
        landing_url=landing_url,
        model_url=model_url,
        source_status=source_status,
        notes=notes,
        collected_at=collected_at,
    )


def build_price_row(
    entry: SourceRegistryEntry,
    *,
    model_name: str,
    model_code: str,
    category: str,
    level_name: str = "",
    level_code: str = "",
    class_name: str = "",
    class_code: str = "",
    year_code: str = "",
    year_label: str = "",
    price_url: str,
    catalog_url: str,
    landing_url: str,
    effective_text: str,
    source_status: str,
    notes: str,
    collected_at: str,
) -> PriceSourceRow:
    return PriceSourceRow(
        source_id=entry.source_id,
        source_kind=entry.source_kind,
        brand=entry.brand,
        model_name=model_name,
        model_code=model_code,
        category=category,
        level_name=level_name,
        level_code=level_code,
        class_name=class_name,
        class_code=class_code,
        year_code=year_code,
        year_label=year_label,
        price_url=price_url,
        catalog_url=catalog_url,
        landing_url=landing_url,
        effective_text=effective_text,
        source_status=source_status,
        notes=notes,
        collected_at=collected_at,
    )


def collect_hyundai(
    context: BrowserContext | None,
    entry: SourceRegistryEntry,
    collected_at: str,
) -> tuple[list[ModelIndexRow], list[PriceSourceRow], list[CrawlAuditRow]]:
    if context is None:
        raise RuntimeError("Hyundai collector requires a Playwright browser context.")

    page = context.new_page()
    models: list[ModelIndexRow] = []
    prices: list[PriceSourceRow] = []
    audits: list[CrawlAuditRow] = []

    try:
        page.goto(entry.landing_url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(3_000)

        body_text = page.locator("body").inner_text(timeout=20_000)
        effective_text = extract_hyundai_effective_text(body_text)
        table_meta = page.eval_on_selector_all(
            "table",
            r"""
            (tables) => tables.map((table) => {
              let el = table.previousElementSibling;
              let category = '';
              while (el && !category) {
                const text = (el.innerText || '').replace(/\s+/g, ' ').trim();
                if (text) category = text;
                el = el.previousElementSibling;
              }
              return {
                category,
                rows: Array.from(table.querySelectorAll('tbody tr')).map((row) => {
                  const firstCell = row.querySelector('th, td');
                  return (firstCell?.innerText || '').replace(/\s+/g, ' ').trim();
                }),
              };
            })
            """,
        )

        table_locators = page.locator("table")
        for table_index in range(table_locators.count()):
            category = normalize_space(table_meta[table_index]["category"])
            row_locators = table_locators.nth(table_index).locator("tbody tr")
            model_names = table_meta[table_index]["rows"]
            for row_index in range(row_locators.count()):
                model_name = normalize_space(model_names[row_index])
                row_locator = row_locators.nth(row_index)
                buttons = row_locator.locator("button")
                button_texts = [normalize_space(buttons.nth(i).inner_text()) for i in range(buttons.count())]

                catalog_url = ""
                price_url = ""

                download_buttons: list[Locator] = []
                for i, text in enumerate(button_texts):
                    if text == "다운로드":
                        download_buttons.append(buttons.nth(i))

                if len(download_buttons) >= 1:
                    try:
                        price_url = capture_download_url(page, download_buttons[-1])
                    except Exception as exc:  # pragma: no cover - network/runtime safety
                        audits.append(
                            CrawlAuditRow(
                                brand=entry.brand,
                                stage="price_url",
                                status="warning",
                                detail=f"{model_name}: {type(exc).__name__}: {exc}",
                                collected_at=collected_at,
                            )
                        )

                if len(download_buttons) >= 2:
                    try:
                        catalog_url = capture_download_url(page, download_buttons[0])
                    except Exception as exc:  # pragma: no cover - network/runtime safety
                        audits.append(
                            CrawlAuditRow(
                                brand=entry.brand,
                                stage="catalog_url",
                                status="warning",
                                detail=f"{model_name}: {type(exc).__name__}: {exc}",
                                collected_at=collected_at,
                            )
                        )

                models.append(
                    build_model_row(
                        entry,
                        model_name=model_name,
                        model_code="",
                        category=category,
                        landing_url=entry.landing_url,
                        model_url=entry.landing_url,
                        source_status="ok",
                        notes="Rendered from Hyundai category tables.",
                        collected_at=collected_at,
                    )
                )
                prices.append(
                    build_price_row(
                        entry,
                        model_name=model_name,
                        model_code="",
                        category=category,
                        level_name="",
                        level_code="",
                        class_name="",
                        class_code="",
                        year_code="",
                        year_label="",
                        price_url=price_url,
                        catalog_url=catalog_url,
                        landing_url=entry.landing_url,
                        effective_text=effective_text,
                        source_status="ok" if price_url else "partial",
                        notes="Price URL captured from Hyundai download button." if price_url else "Price URL discovery needs follow-up.",
                        collected_at=collected_at,
                    )
                )

        audits.append(
            CrawlAuditRow(
                brand=entry.brand,
                stage="collect",
                status="ok",
                detail=f"model_rows={len(models)} price_rows={len(prices)}",
                collected_at=collected_at,
            )
        )
    finally:
        page.close()

    return models, prices, audits


def collect_kia(
    context: BrowserContext | None,
    entry: SourceRegistryEntry,
    collected_at: str,
) -> tuple[list[ModelIndexRow], list[PriceSourceRow], list[CrawlAuditRow]]:
    if context is None:
        raise RuntimeError("Kia collector requires a Playwright browser context.")

    page = context.new_page()
    models_by_key: dict[tuple[str, str, str], ModelIndexRow] = {}
    prices_by_key: dict[tuple[str, str, str], PriceSourceRow] = {}
    audits: list[CrawlAuditRow] = []

    try:
        page.goto(entry.landing_url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(3_000)

        for tab_name in KIA_TABS:
            tab_locator = page.locator("a.vehicis-cate__link", has_text=tab_name)
            if tab_locator.count() == 0:
                continue
            tab_locator.first.click()
            page.wait_for_timeout(1_000)

            items = page.eval_on_selector_all(
                "a[data-model-name]",
                r"""
                (anchors) => anchors
                  .filter((anchor) => {
                    const style = window.getComputedStyle(anchor);
                    return style.display !== 'none' && style.visibility !== 'hidden';
                  })
                  .map((anchor) => ({
                    text: (anchor.innerText || anchor.textContent || '').replace(/\s+/g, ' ').trim(),
                    href: anchor.href,
                    modelName: anchor.getAttribute('data-model-name') || '',
                    linkLabel: anchor.getAttribute('data-link-label') || '',
                  }))
                  .filter((item) => item.modelName)
                """,
            )

            grouped: dict[tuple[str, str], dict[str, str]] = {}
            for item in items:
                raw_model_name = item["modelName"]
                if "|" in raw_model_name:
                    model_name, model_code = raw_model_name.split("|", 1)
                else:
                    model_name, model_code = raw_model_name, ""
                key = (normalize_space(model_name), normalize_space(model_code))
                bundle = grouped.setdefault(
                    key,
                    {
                        "model_url": "",
                        "catalog_url": "",
                        "price_url": "",
                    },
                )
                href = item["href"]
                text = normalize_space(item["text"])
                link_label = normalize_space(item["linkLabel"])

                if "/pdf/price/" in href:
                    bundle["price_url"] = href
                elif "/pdf/catalog/" in href and "_mo_" not in href:
                    bundle["catalog_url"] = href
                elif text and text == key[0]:
                    bundle["model_url"] = href
                elif link_label.startswith("국문가격표"):
                    bundle["price_url"] = href
                elif link_label.startswith("국문카탈로그") and "_mo_" not in href:
                    bundle["catalog_url"] = href

            for (model_name, model_code), bundle in grouped.items():
                row_key = (tab_name, model_name, model_code)
                models_by_key[row_key] = build_model_row(
                    entry,
                    model_name=model_name,
                    model_code=model_code,
                    category=tab_name,
                    landing_url=entry.landing_url,
                    model_url=bundle["model_url"] or entry.landing_url,
                    source_status="ok",
                    notes="Rendered from Kia visible tab card anchors.",
                    collected_at=collected_at,
                )
                prices_by_key[row_key] = build_price_row(
                    entry,
                    model_name=model_name,
                    model_code=model_code,
                    category=tab_name,
                    level_name="",
                    level_code="",
                    class_name="",
                    class_code="",
                    year_code="",
                    year_label="",
                    price_url=bundle["price_url"],
                    catalog_url=bundle["catalog_url"],
                    landing_url=entry.landing_url,
                    effective_text="",
                    source_status="ok" if bundle["price_url"] else "partial",
                    notes="Price URL discovered from Kia rendered anchor." if bundle["price_url"] else "Price URL discovery needs follow-up.",
                    collected_at=collected_at,
                )

        audits.append(
            CrawlAuditRow(
                brand=entry.brand,
                stage="collect",
                status="ok",
                detail=f"model_rows={len(models_by_key)} price_rows={len(prices_by_key)}",
                collected_at=collected_at,
            )
        )
    finally:
        page.close()

    return list(models_by_key.values()), list(prices_by_key.values()), audits


def collect_renault(
    context: BrowserContext | None,
    entry: SourceRegistryEntry,
    collected_at: str,
) -> tuple[list[ModelIndexRow], list[PriceSourceRow], list[CrawlAuditRow]]:
    if context is None:
        raise RuntimeError("Renault collector requires a Playwright browser context.")

    page = context.new_page()
    models: list[ModelIndexRow] = []
    prices: list[PriceSourceRow] = []
    audits: list[CrawlAuditRow] = []

    try:
        page.goto(entry.landing_url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(3_000)

        card_count = page.evaluate(
            r"""
            () => {
              const seen = new Set();
              let idx = 0;
              for (const el of document.querySelectorAll('div')) {
                const text = (el.innerText || '').replace(/\s+/g, ' ').trim();
                const title = el.querySelector('p');
                const buttons = el.querySelectorAll('button');
                if (!title || buttons.length < 2 || text.length > 120) {
                  continue;
                }
                const modelName = (title.innerText || '').replace(/\s+/g, ' ').trim();
                if (!modelName || seen.has(modelName)) {
                  continue;
                }
                if (!text.includes('다운로드') || !text.includes('가격표')) {
                  continue;
                }
                el.setAttribute('data-model-card-index', String(idx));
                seen.add(modelName);
                idx += 1;
              }
              return idx;
            }
            """,
        )

        for card_index in range(card_count):
            card = page.locator(f'[data-model-card-index="{card_index}"]')
            model_name = normalize_space(card.locator("p").first.inner_text())
            if model_name == "전체 모델":
                continue
            buttons = card.locator("button")
            catalog_url = ""
            price_url = ""
            for button_index in range(buttons.count()):
                button = buttons.nth(button_index)
                label = normalize_space(button.inner_text())
                if "가격표" in label and "다운로드" in label:
                    price_url = capture_download_url(page, button)
                elif "카탈로그" in label and "다운로드" in label and "액세서리" not in label:
                    catalog_url = capture_download_url(page, button)

            models.append(
                build_model_row(
                    entry,
                    model_name=model_name,
                    model_code="",
                    category="domestic",
                    landing_url=entry.landing_url,
                    model_url=entry.landing_url,
                    source_status="ok",
                    notes="Rendered from Renault download cards.",
                    collected_at=collected_at,
                )
            )
            prices.append(
                build_price_row(
                    entry,
                    model_name=model_name,
                    model_code="",
                    category="domestic",
                    level_name="",
                    level_code="",
                    class_name="",
                    class_code="",
                    year_code="",
                    year_label="",
                    price_url=price_url,
                    catalog_url=catalog_url,
                    landing_url=entry.landing_url,
                    effective_text="",
                    source_status="ok" if price_url else "partial",
                    notes="Price URL captured from Renault download button." if price_url else "Price URL discovery needs follow-up.",
                    collected_at=collected_at,
                )
            )

        audits.append(
            CrawlAuditRow(
                brand=entry.brand,
                stage="collect",
                status="ok",
                detail=f"model_rows={len(models)} price_rows={len(prices)}",
                collected_at=collected_at,
            )
        )
    finally:
        page.close()

    return models, prices, audits


def collect_kgm(
    context: BrowserContext | None,
    entry: SourceRegistryEntry,
    collected_at: str,
) -> tuple[list[ModelIndexRow], list[PriceSourceRow], list[CrawlAuditRow]]:
    if context is None:
        raise RuntimeError("KGM collector requires a Playwright browser context.")

    page = context.new_page()
    models: list[ModelIndexRow] = []
    prices: list[PriceSourceRow] = []
    audits: list[CrawlAuditRow] = []

    try:
        page.goto(entry.landing_url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(3_000)
        card_count = page.evaluate(
            r"""
            () => {
              let idx = 0;
              for (const el of document.querySelectorAll('li.download__item')) {
                el.setAttribute('data-model-card-index', String(idx));
                idx += 1;
              }
              return idx;
            }
            """,
        )

        for card_index in range(card_count):
            card = page.locator(f'[data-model-card-index="{card_index}"]')
            info_text = normalize_space(card.locator(".download__item-info").inner_text())
            model_name = normalize_space(info_text.replace("카탈로그", "").replace("가격표", ""))
            buttons = card.locator("button.button")
            catalog_url = ""
            price_url = ""
            for button_index in range(buttons.count()):
                button = buttons.nth(button_index)
                label = normalize_space(button.inner_text())
                if label == "카탈로그":
                    catalog_url = capture_download_url(page, button)
                elif label == "가격표":
                    price_url = capture_download_url(page, button)

            models.append(
                build_model_row(
                    entry,
                    model_name=model_name,
                    model_code="",
                    category="domestic",
                    landing_url=entry.landing_url,
                    model_url=entry.landing_url,
                    source_status="ok",
                    notes="Rendered from KGM download cards.",
                    collected_at=collected_at,
                )
            )
            prices.append(
                build_price_row(
                    entry,
                    model_name=model_name,
                    model_code="",
                    category="domestic",
                    level_name="",
                    level_code="",
                    class_name="",
                    class_code="",
                    year_code="",
                    year_label="",
                    price_url=price_url,
                    catalog_url=catalog_url,
                    landing_url=entry.landing_url,
                    effective_text="",
                    source_status="ok" if price_url else "partial",
                    notes="Price URL captured from KGM download button." if price_url else "Price URL discovery needs follow-up.",
                    collected_at=collected_at,
                )
            )

        audits.append(
            CrawlAuditRow(
                brand=entry.brand,
                stage="collect",
                status="ok",
                detail=f"model_rows={len(models)} price_rows={len(prices)}",
                collected_at=collected_at,
            )
        )
    finally:
        page.close()

    return models, prices, audits


def collect_chevrolet(
    _context: BrowserContext | None,
    entry: SourceRegistryEntry,
    collected_at: str,
) -> tuple[list[ModelIndexRow], list[PriceSourceRow], list[CrawlAuditRow]]:
    models: list[ModelIndexRow] = []
    prices: list[PriceSourceRow] = []
    audits: list[CrawlAuditRow] = []

    try:
        html = fetch_html(entry.landing_url)
        text = normalize_space(BeautifulSoup(html, "html.parser").get_text(" "))
        for model_name, category in CHEVROLET_MODELS:
            status = "ok" if model_name in text else "manual_review"
            note = "Visible text confirmed from Chevrolet landing page." if status == "ok" else "Model needs manual confirmation."
            models.append(
                build_model_row(
                    entry,
                    model_name=model_name,
                    model_code="",
                    category=category,
                    landing_url=entry.landing_url,
                    model_url=entry.landing_url,
                    source_status=status,
                    notes=note,
                    collected_at=collected_at,
                )
            )
            prices.append(
                build_price_row(
                    entry,
                    model_name=model_name,
                    model_code="",
                    category=category,
                    level_name="",
                    level_code="",
                    class_name="",
                    class_code="",
                    year_code="",
                    year_label="",
                    price_url="",
                    catalog_url="",
                    landing_url=entry.landing_url,
                    effective_text="",
                    source_status="manual_review",
                    notes="Rendered access is blocked for Chevrolet. Price URLs need manual follow-up.",
                    collected_at=collected_at,
                )
            )

        audits.append(
            CrawlAuditRow(
                brand=entry.brand,
                stage="collect",
                status="warning",
                detail="Chevrolet price sources are manual_review because rendered download access is blocked.",
                collected_at=collected_at,
            )
        )
    except URLError as exc:
        audits.append(
            CrawlAuditRow(
                brand=entry.brand,
                stage="collect",
                status="error",
                detail=f"URLError: {exc}",
                collected_at=collected_at,
            )
        )

    return models, prices, audits


def collect_bobaedream_archive(
    _context: BrowserContext | None,
    entry: SourceRegistryEntry,
    collected_at: str,
    *,
    include_price_index: bool,
    price_model_limit: int | None,
) -> tuple[list[ModelIndexRow], list[PriceSourceRow], list[CrawlAuditRow]]:
    models: list[ModelIndexRow] = []
    prices: list[PriceSourceRow] = []
    audits: list[CrawlAuditRow] = []

    maker_code = entry.external_code
    model_options = fetch_boba_options("model", maker_code)
    LOGGER.info(
        "Bobaedream archive model scan: brand=%s total_models=%s include_price_index=%s",
        entry.brand,
        len(model_options),
        include_price_index,
    )
    model_count = 0
    for model_code, model_name in model_options:
        price_rows_before_model = len(prices)
        models.append(
            build_model_row(
                entry,
                model_name=model_name,
                model_code=model_code,
                category="archive",
                landing_url=entry.landing_url,
                model_url=build_boba_query_url(maker_no=maker_code, model_no=model_code),
                source_status="ok",
                notes="Historical model discovered from Bobaedream archive selector.",
                collected_at=collected_at,
            )
        )
        model_count += 1

        if not include_price_index:
            pass
        elif price_model_limit is None or model_count <= price_model_limit:
            try:
                level_options = fetch_boba_options("level", model_code)
            except Exception as exc:  # pragma: no cover - network/runtime safety
                audits.append(
                    CrawlAuditRow(
                        brand=entry.brand,
                        stage="archive_level",
                        status="warning",
                        detail=f"{model_name}: {type(exc).__name__}: {exc}",
                        collected_at=collected_at,
                    )
                )
                level_options = []
            for level_code, level_name in level_options:
                try:
                    class_options = fetch_boba_options("class", level_code)
                except Exception as exc:  # pragma: no cover - network/runtime safety
                    audits.append(
                        CrawlAuditRow(
                            brand=entry.brand,
                            stage="archive_class",
                            status="warning",
                            detail=f"{model_name}/{level_name}: {type(exc).__name__}: {exc}",
                            collected_at=collected_at,
                        )
                    )
                    class_options = []
                if not class_options:
                    prices.append(
                        build_price_row(
                            entry,
                            model_name=model_name,
                            model_code=model_code,
                            category="archive",
                            level_name=level_name,
                            level_code=level_code,
                            class_name="",
                            class_code="",
                            year_code="",
                            year_label="",
                            price_url=build_boba_query_url(maker_no=maker_code, model_no=model_code, level_no=level_code),
                            catalog_url="",
                            landing_url=entry.landing_url,
                            effective_text="",
                            source_status="ok",
                            notes="Historical trim source URL from Bobaedream archive.",
                            collected_at=collected_at,
                        )
                    )
                    continue

                for class_code, class_name in class_options:
                    query_url = build_boba_query_url(
                        maker_no=maker_code,
                        model_no=model_code,
                        level_no=level_code,
                        level2_no=class_code,
                    )
                    try:
                        query_html = fetch_html(query_url)
                    except Exception as exc:  # pragma: no cover - network/runtime safety
                        audits.append(
                            CrawlAuditRow(
                                brand=entry.brand,
                                stage="archive_query",
                                status="warning",
                                detail=f"{model_name}/{level_name}/{class_name}: {type(exc).__name__}: {exc}",
                                collected_at=collected_at,
                            )
                        )
                        continue

                    year_options = extract_select_options(query_html, "year_no")
                    year_options = [(year_code, year_label) for year_code, year_label in year_options if year_code]
                    if not year_options:
                        prices.append(
                            build_price_row(
                                entry,
                                model_name=model_name,
                                model_code=model_code,
                                category="archive",
                                level_name=level_name,
                                level_code=level_code,
                                class_name=class_name,
                                class_code=class_code,
                                year_code="",
                                year_label="",
                                price_url=query_url,
                                catalog_url="",
                                landing_url=entry.landing_url,
                                effective_text="",
                                source_status="ok",
                                notes="Historical class source URL from Bobaedream archive.",
                                collected_at=collected_at,
                            )
                        )
                        continue

                    for year_code, year_label in year_options:
                        prices.append(
                            build_price_row(
                                entry,
                                model_name=model_name,
                                model_code=model_code,
                                category="archive",
                                level_name=level_name,
                                level_code=level_code,
                                class_name=class_name,
                                class_code=class_code,
                                year_code=year_code,
                                year_label=year_label,
                                price_url=build_boba_query_url(
                                    maker_no=maker_code,
                                    model_no=model_code,
                                    level_no=level_code,
                                    level2_no=class_code,
                                    year_no=year_code,
                                ),
                                catalog_url="",
                                landing_url=entry.landing_url,
                                effective_text=year_label,
                                source_status="ok",
                                notes="Historical year-specific source URL from Bobaedream archive.",
                                collected_at=collected_at,
                            )
                        )

        if model_count == 1 or model_count % 25 == 0 or model_count == len(model_options):
            LOGGER.info(
                "Bobaedream archive progress: brand=%s models_completed=%s/%s price_rows_total=%s added_for_model=%s current_model=%s",
                entry.brand,
                model_count,
                len(model_options),
                len(prices),
                len(prices) - price_rows_before_model,
                model_name,
            )

    detail = f"model_rows={len(models)} price_rows={len(prices)}"
    if include_price_index and price_model_limit is not None:
        detail += f" price_model_limit={price_model_limit}"
    audits.append(
        CrawlAuditRow(
            brand=entry.brand,
            stage="collect",
            status="ok",
            detail=detail,
            collected_at=collected_at,
        )
    )
    LOGGER.info(
        "Bobaedream archive complete: brand=%s model_rows=%s price_rows=%s",
        entry.brand,
        len(models),
        len(prices),
    )
    return models, prices, audits


def fetch_boba_options(depth: str, no: str) -> list[tuple[str, str]]:
    body = post_form(
        "https://m.bobaedream.co.kr/calculator/ajax_depth",
        {"depth": depth, "no": no},
    )
    html = json.loads(body)
    soup = BeautifulSoup(f"<select>{html}</select>", "html.parser")
    options: list[tuple[str, str]] = []
    for option in soup.select("option"):
        value = normalize_space(str(option.get("value", "") or ""))
        text = normalize_space(option.get_text())
        if not value:
            continue
        options.append((value, text))
    return options


def post_form(url: str, payload: dict[str, str]) -> str:
    encoded = urlencode(payload).encode()
    request = Request(
        url,
        data=encoded,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        },
    )
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            with urlopen(request, timeout=20) as response:
                return response.read().decode("utf-8", errors="replace")
        except RETRYABLE_FETCH_ERRORS as exc:
            last_error = exc
            if attempt == 3:
                raise
            time.sleep(0.5 * attempt)
    if last_error is not None:
        raise last_error
    raise RuntimeError(f"Failed to post url: {url}")


def build_boba_query_url(
    *,
    maker_no: str,
    model_no: str,
    level_no: str | None = None,
    level2_no: str | None = None,
    year_no: str | None = None,
) -> str:
    params = {
        "maker_no": maker_no,
        "model_no": model_no,
        "level_no": level_no or "",
        "level2_no": level2_no or "",
        "year_no": year_no or "",
    }
    return f"https://m.bobaedream.co.kr/calculator/carinfo?{urlencode(params)}"


def extract_select_options(html: str, select_name: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    select = soup.select_one(f'select[name="{select_name}"]')
    if select is None:
        return []
    return [
        (normalize_space(str(option.get("value", "") or "")), normalize_space(option.get_text()))
        for option in select.select("option")
    ]


def capture_download_url(page: Page, locator: Locator) -> str:
    with page.expect_download(timeout=15_000) as download_info:
        locator.click()
    download = download_info.value
    return download.url


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            with urlopen(request, timeout=20) as response:
                return response.read().decode("utf-8", errors="replace")
        except RETRYABLE_FETCH_ERRORS as exc:
            last_error = exc
            if attempt == 3:
                raise
            time.sleep(0.5 * attempt)
    if last_error is not None:
        raise last_error
    raise RuntimeError(f"Failed to fetch url: {url}")


def extract_hyundai_effective_text(text: str) -> str:
    match = re.search(r"\d{4}년\s*\d{1,2}월\s*기준\s*\('[0-9.]+\s*업데이트\)", text)
    if not match:
        return ""
    return normalize_space(match.group(0))


def normalize_space(value: str) -> str:
    return " ".join(value.split())


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        if path.name == "model_index.csv":
            fieldnames = list(ModelIndexRow.__annotations__.keys())
        elif path.name == "price_source_index.csv":
            fieldnames = list(PriceSourceRow.__annotations__.keys())
        elif path.name == "crawl_audit.csv":
            fieldnames = list(CrawlAuditRow.__annotations__.keys())
        else:
            fieldnames = []
    else:
        fieldnames = list(rows[0].keys())

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summarize_price_rows(rows: list[PriceSourceRow]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter[row.brand] += 1
    return dict(counter)
