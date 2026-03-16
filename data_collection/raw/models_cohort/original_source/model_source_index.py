from __future__ import annotations

import csv
import re
from pathlib import Path


MODEL_SOURCE_HEADERS = [
    "brand",
    "archive_source_id",
    "archive_model_name",
    "archive_model_code",
    "archive_model_url",
    "archive_price_row_count",
    "primary_source_kind",
    "primary_has_launch_price",
    "primary_has_trim_selector",
    "primary_has_displacement",
    "official_source_id",
    "official_model_name",
    "official_model_url",
    "official_price_url",
    "official_catalog_url",
    "official_effective_text",
    "supplement_match_status",
    "supplement_match_reason",
    "supplement_match_score",
]


TRANSLITERATION_ALIASES = {
    "renault": {
        "filante": ("필랑트",),
        "scenic": ("세닉",),
        "grandkoleos": ("그랑콜레오스",),
        "arkana": ("아르카나",),
    },
    "kgm": {
        "액티언하이브리드": ("액티언2세대",),
        "토레스하이브리드": ("더뉴토레스", "토레스"),
    },
}


RECENT_PREFIXES = ("디올뉴", "더뉴", "올뉴", "신형", "2세대")
OLD_GENERATION_TOKENS = (
    "ig",
    "hg",
    "tg",
    "xg",
    "dm",
    "cm",
    "ad",
    "md",
    "hd",
    "xd",
    "pd",
    "js",
    "dh",
    "tm",
)


def build_model_source_index(
    model_index_csv: Path,
    price_source_index_csv: Path,
    output_csv: Path,
) -> list[dict[str, str]]:
    with model_index_csv.open("r", encoding="utf-8", newline="") as handle:
        model_rows = list(csv.DictReader(handle))
    with price_source_index_csv.open("r", encoding="utf-8", newline="") as handle:
        price_rows = list(csv.DictReader(handle))

    archive_rows = [row for row in model_rows if row["source_kind"] == "market_archive_index"]
    official_rows = [row for row in model_rows if row["source_kind"] == "official_catalog_index"]

    archive_price_counts: dict[tuple[str, str], int] = {}
    for row in price_rows:
        if row["source_kind"] != "market_archive_index":
            continue
        key = (row["brand"], row["model_code"])
        archive_price_counts[key] = archive_price_counts.get(key, 0) + 1

    official_price_lookup: dict[tuple[str, str], dict[str, str]] = {}
    for row in price_rows:
        if row["source_kind"] != "official_catalog_index":
            continue
        key = (row["brand"], row["model_name"])
        official_price_lookup[key] = row

    archive_by_brand: dict[str, list[dict[str, str]]] = {}
    for row in archive_rows:
        archive_by_brand.setdefault(row["brand"], []).append(row)

    supplement_by_archive_code: dict[tuple[str, str], dict[str, str]] = {}
    for official_row in official_rows:
        match = find_best_archive_match(official_row, archive_by_brand.get(official_row["brand"], []))
        if match is None:
            continue
        archive_row, score, reason = match
        key = (archive_row["brand"], archive_row["model_code"])
        current = supplement_by_archive_code.get(key)
        if current is None or score > int(current["supplement_match_score"]):
            price_row = official_price_lookup.get((official_row["brand"], official_row["model_name"]), {})
            supplement_by_archive_code[key] = {
                "official_source_id": official_row["source_id"],
                "official_model_name": official_row["model_name"],
                "official_model_url": official_row["model_url"],
                "official_price_url": price_row.get("price_url", ""),
                "official_catalog_url": price_row.get("catalog_url", ""),
                "official_effective_text": price_row.get("effective_text", ""),
                "supplement_match_status": "matched",
                "supplement_match_reason": reason,
                "supplement_match_score": str(score),
            }

    output_rows: list[dict[str, str]] = []
    for archive_row in archive_rows:
        key = (archive_row["brand"], archive_row["model_code"])
        supplement = supplement_by_archive_code.get(
            key,
            {
                "official_source_id": "",
                "official_model_name": "",
                "official_model_url": "",
                "official_price_url": "",
                "official_catalog_url": "",
                "official_effective_text": "",
                "supplement_match_status": "unmatched",
                "supplement_match_reason": "",
                "supplement_match_score": "0",
            },
        )
        output_rows.append(
            {
                "brand": archive_row["brand"],
                "archive_source_id": archive_row["source_id"],
                "archive_model_name": archive_row["model_name"],
                "archive_model_code": archive_row["model_code"],
                "archive_model_url": archive_row["model_url"],
                "archive_price_row_count": str(archive_price_counts.get(key, 0)),
                "primary_source_kind": archive_row["source_kind"],
                "primary_has_launch_price": "Y",
                "primary_has_trim_selector": "Y",
                "primary_has_displacement": "Y",
                **supplement,
            }
        )

    write_rows(output_csv, output_rows, MODEL_SOURCE_HEADERS)
    return output_rows


def find_best_archive_match(
    official_row: dict[str, str],
    archive_rows: list[dict[str, str]],
) -> tuple[dict[str, str], int, str] | None:
    best: tuple[dict[str, str], int, str] | None = None
    official_keys = official_candidate_keys(official_row["brand"], official_row["model_name"])
    official_full = normalize_model_key(official_row["brand"], official_row["model_name"])

    for archive_row in archive_rows:
        archive_full = normalize_model_key(archive_row["brand"], archive_row["model_name"])
        archive_recent = archive_has_recent_signal(archive_row["model_name"])
        score = 0
        reason = ""

        if archive_full in official_keys:
            score = 100
            reason = "exact_or_alias"
        elif any(key and archive_full.startswith(key) for key in official_keys):
            score = 92
            reason = "archive_prefixed_current"
        elif official_full and archive_full and official_full in archive_full and archive_recent:
            score = 88
            reason = "current_prefix_family"
        elif official_full and archive_full and archive_full == strip_recent_prefix(official_full):
            score = 85
            reason = "prefix_stripped_exact"

        if score == 0:
            continue
        if any(token in archive_full for token in OLD_GENERATION_TOKENS) and not archive_recent:
            score -= 20
        if best is None or score > best[1]:
            best = (archive_row, score, reason)

    if best is None or best[1] < 80:
        return None
    return best


def official_candidate_keys(brand: str, model_name: str) -> set[str]:
    full = normalize_model_key(brand, model_name)
    keys = {full}
    base = strip_recent_prefix(full)
    if base:
        keys.add(base)
        for prefix in RECENT_PREFIXES:
            keys.add(prefix + base)
    for alias in TRANSLITERATION_ALIASES.get(brand, {}).get(full, ()):  # brand-specific aliases
        alias_key = normalize_model_key(brand, alias)
        keys.add(alias_key)
        keys.add(strip_recent_prefix(alias_key))
        for prefix in RECENT_PREFIXES:
            keys.add(prefix + strip_recent_prefix(alias_key))
    return {key for key in keys if key}


def normalize_model_key(brand: str, model_name: str) -> str:
    value = model_name.lower().strip()
    replacements = {
        " nline 포함": "",
        " n-line 포함": "",
        " hybrid": " 하이브리드",
        " electric": " 일렉트릭",
        " new": "",
        " ii ": " 2 ",
        "ⅱ": "2",
        "ⅲ": "3",
        " ii": " 2",
        " Ⅱ": " 2",
        " Ⅲ": " 3",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = re.sub(r"\[[^\]]+\]", "", value)
    value = re.sub(r"\([^\)]*\)", "", value)
    value = value.replace("기아", "")
    value = value.replace("kg mobility", "kgm")
    value = value.replace("모빌리티", "")
    value = re.sub(r"[^0-9a-z가-힣]+", "", value)
    return value


def archive_has_recent_signal(model_name: str) -> bool:
    normalized = normalize_model_key("", model_name)
    return any(normalized.startswith(prefix) for prefix in RECENT_PREFIXES)


def strip_recent_prefix(value: str) -> str:
    for prefix in RECENT_PREFIXES:
        if value.startswith(prefix):
            return value[len(prefix) :]
    return value


def write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
