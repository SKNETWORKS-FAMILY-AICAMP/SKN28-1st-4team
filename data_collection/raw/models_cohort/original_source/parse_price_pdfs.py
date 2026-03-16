# pyright: reportMissingImports=false

from __future__ import annotations

import csv
import re
import ssl
from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen

from pypdf import PdfReader


@dataclass(slots=True)
class PriceTextRow:
    brand: str
    model_name: str
    model_code: str
    category: str
    price_url: str
    pdf_cache_path: str
    text_cache_path: str
    page_count: int
    extraction_status: str
    extracted_at: str


@dataclass(slots=True)
class VariantSeedRow:
    brand: str
    model_name: str
    variant_context: str
    trim_name: str
    fuel_type: str
    powertrain_type: str
    displacement_cc: str
    drive_type: str
    transmission: str
    body_type: str
    base_price_text: str
    base_price_krw: str
    source_url: str
    parse_strategy: str
    parse_confidence: str


SECTION_BANNED = {
    "선택품목",
    "판매가격",
    "기본 품목",
    "공통",
    "구분",
    "정부 신고연비",
    "패키지 옵션 세 부 사 양",
    "EXTERIOR COLORS",
    "INTERIOR COLORS",
    "WHEELS",
}

TRIM_BANNED_SUBSTRINGS = (
    "선택품목",
    "판매가격",
    "기본 품목",
    "공통",
    "가격표",
    "정부 신고연비",
    "패키지",
    "옵션",
    "세제",
    "공급가액",
    "친환경차",
    "EXTERIOR",
    "INTERIOR",
    "WHEELS",
    "인포테인먼트",
    "컴포트",
    "스타일",
    "드라이브 와이즈",
)


def cache_price_texts(
    price_rows: list[dict[str, str]],
    output_dir: Path,
    extracted_at: str,
    max_price_per_brand: int | None = None,
) -> tuple[list[PriceTextRow], list[VariantSeedRow]]:
    cache_pdf_dir = output_dir / "cache" / "pdf"
    cache_text_dir = output_dir / "cache" / "text"
    cache_pdf_dir.mkdir(parents=True, exist_ok=True)
    cache_text_dir.mkdir(parents=True, exist_ok=True)

    per_brand_count: dict[str, int] = {}
    text_rows: list[PriceTextRow] = []
    variant_rows: list[VariantSeedRow] = []

    for row in price_rows:
        brand = row["brand"]
        price_url = row["price_url"]
        if not price_url:
            continue
        if not price_url.lower().endswith(".pdf"):
            continue
        if max_price_per_brand is not None and per_brand_count.get(brand, 0) >= max_price_per_brand:
            continue

        pdf_bytes = fetch_bytes(price_url)
        pdf_path = cache_pdf_dir / f"{brand}__{slugify(row['model_name'])}.pdf"
        text_path = cache_text_dir / f"{brand}__{slugify(row['model_name'])}.txt"
        pdf_path.write_bytes(pdf_bytes)

        page_texts = extract_pdf_texts(pdf_bytes)
        joined_text = "\n\n".join(page_texts)
        text_path.write_text(joined_text, encoding="utf-8")

        text_rows.append(
            PriceTextRow(
                brand=brand,
                model_name=row["model_name"],
                model_code=row["model_code"],
                category=row["category"],
                price_url=price_url,
                pdf_cache_path=str(pdf_path),
                text_cache_path=str(text_path),
                page_count=len(page_texts),
                extraction_status="ok",
                extracted_at=extracted_at,
            )
        )
        variant_rows.extend(parse_variant_seed_rows(row, page_texts))
        per_brand_count[brand] = per_brand_count.get(brand, 0) + 1

    write_rows(output_dir / "price_text_index.csv", [asdict(row) for row in text_rows], PriceTextRow)
    write_rows(output_dir / "variant_seed_raw.csv", [asdict(row) for row in dedupe_variant_rows(variant_rows)], VariantSeedRow)
    return text_rows, variant_rows


def parse_variant_seed_rows(price_row: dict[str, str], page_texts: list[str]) -> list[VariantSeedRow]:
    if price_row["brand"] in {"hyundai", "renault"}:
        return []

    variant_rows: list[VariantSeedRow] = []
    seen: set[tuple[str, str, str]] = set()

    for page_text in page_texts:
        current_context = ""
        lines = split_clean_lines(page_text)
        for index, line in enumerate(lines):
            context_candidate = extract_context_label(line)
            if context_candidate:
                current_context = context_candidate

            match = match_trim_price(lines, index)
            if match is None:
                continue

            trim_name, price_text = match
            if price_text_to_krw(price_text) < 10_000_000:
                continue
            normalized_key = (price_row["model_name"], current_context, trim_name)
            if normalized_key in seen:
                continue
            seen.add(normalized_key)
            variant_rows.append(
                VariantSeedRow(
                    brand=price_row["brand"],
                    model_name=price_row["model_name"],
                    variant_context=current_context,
                    trim_name=trim_name,
                    fuel_type="",
                    powertrain_type="",
                    displacement_cc="",
                    drive_type="",
                    transmission="",
                    body_type="",
                    base_price_text=price_text,
                    base_price_krw=str(price_text_to_krw(price_text)),
                    source_url=price_row["price_url"],
                    parse_strategy="heuristic_line_match",
                    parse_confidence="low",
                )
            )

    return variant_rows


def extract_pdf_texts(pdf_bytes: bytes) -> list[str]:
    reader = PdfReader(BytesIO(pdf_bytes))
    page_texts: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text(extraction_mode="layout") or page.extract_text() or ""
        except TypeError:
            text = page.extract_text() or ""
        page_texts.append(text)
    return page_texts


def fetch_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=30) as response:
            return response.read()
    except OSError:
        insecure_context = ssl._create_unverified_context()
        with urlopen(request, timeout=30, context=insecure_context) as response:
            return response.read()


def split_clean_lines(text: str) -> list[str]:
    text = re.sub(r"(?<=[A-Za-z가-힣])(?=\d{1,3},\d{3}(?:,\d{3})?)", " ", text)
    text = re.sub(r"(?<=[A-Za-z가-힣])(?=\d{1,2},\d{3}만)", " ", text)
    text = re.sub(r"(?<=\))(?=[A-Za-z가-힣])", " ", text)
    lines = []
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        if line:
            lines.append(line)
    return lines


def extract_context_label(line: str) -> str:
    cleaned = line.replace("(단위 : 원)", "").strip()
    if not cleaned:
        return ""
    if cleaned in SECTION_BANNED:
        return ""
    if any(char.isdigit() for char in cleaned) and "," in cleaned:
        return ""
    if any(token in cleaned for token in ("승용", "밴", "하이브리드", "가솔린", "디젤", "전기", "Electric", "터보")) and len(cleaned) <= 25:
        return cleaned
    return ""


def match_trim_price(lines: list[str], index: int) -> tuple[str, str] | None:
    line = lines[index]
    inline_match = match_inline_trim_price(line)
    if inline_match is not None:
        return inline_match

    trim_name = extract_standalone_trim(line)
    if not trim_name:
        return None

    previous_price = nearest_price_line(lines, index, direction=-1)
    if previous_price is not None:
        return trim_name, previous_price

    next_price = nearest_price_line(lines, index, direction=1)
    if next_price is not None:
        return trim_name, next_price

    return None


def match_inline_trim_price(line: str) -> tuple[str, str] | None:
    patterns = (
        re.compile(r"^(?P<trim>[A-Za-z가-힣0-9&+\-\/(). ]{1,24})\s+(?P<price>\d{1,3}(?:,\d{3})+)(?:\b|\s)"),
        re.compile(r"^(?P<trim>[A-Za-z가-힣0-9&+\-\/(). ]{1,24})\s+(?P<price>\d{1,2},\d{3}만)(?:\b|\s)"),
    )
    for pattern in patterns:
        match = pattern.match(line)
        if not match:
            continue
        trim = normalize_space(match.group("trim"))
        if not is_plausible_trim(trim):
            return None
        return trim, normalize_space(match.group("price"))
    return None


def extract_standalone_trim(line: str) -> str:
    trimmed = normalize_space(line)
    if not is_plausible_trim(trimmed):
        return ""
    if price_only(trimmed) is not None:
        return ""
    return trimmed


def nearest_price_line(lines: list[str], index: int, direction: int) -> str | None:
    offsets = range(1, 4)
    for offset in offsets:
        candidate_index = index + (offset * direction)
        if candidate_index < 0 or candidate_index >= len(lines):
            continue
        price_text = price_only(lines[candidate_index])
        if price_text is not None:
            return price_text
    return None


def price_only(line: str) -> str | None:
    match = re.match(r"^(?P<price>\d{1,3}(?:,\d{3})+)(?:\s*\([\d,]+\))?(?:\b|\s)", line)
    if match:
        return normalize_space(match.group("price"))
    match = re.match(r"^(?P<price>\d{1,2},\d{3}만)(?:\b|\s)", line)
    if match:
        return normalize_space(match.group("price"))
    return None


def is_plausible_trim(value: str) -> bool:
    if not value or len(value) > 24:
        return False
    if any(token in value for token in TRIM_BANNED_SUBSTRINGS):
        return False
    if ":" in value or "•" in value or "▶" in value or "" == value.strip():
        return False
    if value.count(" ") > 3:
        return False
    numeric_groups = re.findall(r"\d+", value)
    if len(numeric_groups) > 2:
        return False
    if re.search(r"[가-힣A-Za-z]", value) is None:
        return False
    return True


def price_text_to_krw(value: str) -> int:
    if value.endswith("만"):
        return int(value[:-1].replace(",", "")) * 10_000
    return int(value.replace(",", ""))


def dedupe_variant_rows(rows: list[VariantSeedRow]) -> list[VariantSeedRow]:
    deduped: dict[tuple[str, str, str, str], VariantSeedRow] = {}
    for row in rows:
        key = (row.brand, row.model_name, row.variant_context, row.trim_name)
        deduped.setdefault(key, row)
    return sorted(
        deduped.values(),
        key=lambda row: (row.brand, row.model_name, row.variant_context, row.trim_name),
    )


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9가-힣]+", "-", value)
    return value.strip("-") or "unknown"


def normalize_space(value: str) -> str:
    return " ".join(value.split())


def write_rows(path: Path, rows: list[dict[str, object]], schema: type[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(schema.__annotations__.keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
