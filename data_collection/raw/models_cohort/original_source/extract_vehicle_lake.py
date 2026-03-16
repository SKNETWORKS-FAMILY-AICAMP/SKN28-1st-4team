from __future__ import annotations

import csv
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import unquote

from bs4 import BeautifulSoup
from bs4.element import Tag

from collect_sources import fetch_html, normalize_space


LOGGER = logging.getLogger(__name__)


VEHICLE_LAKE_HEADERS = [
    "brand",
    "source_id",
    "source_kind",
    "model_name",
    "model_code",
    "level_name",
    "level_code",
    "class_name",
    "class_code",
    "year_code",
    "year_label",
    "primary_source_url",
    "supplement_official_price_url",
    "supplement_official_catalog_url",
    "launch_price_text",
    "launch_price_krw",
    "engine_type",
    "cylinder_count",
    "displacement_cc_text",
    "displacement_cc",
    "max_output_text",
    "max_output_ps",
    "max_torque_text",
    "max_torque_kgm",
    "drive_type",
    "brake_type",
    "suspension_type",
    "steering_type",
    "body_size_text",
    "body_length_mm",
    "body_width_mm",
    "body_height_mm",
    "wheelbase_mm",
    "fuel_type",
    "combined_efficiency_text",
    "combined_efficiency_kmpl",
    "city_efficiency_text",
    "city_efficiency_kmpl",
    "highway_efficiency_text",
    "highway_efficiency_kmpl",
    "co2_text",
    "co2_gkm",
    "fuel_tank_l",
    "warranty_basic",
    "warranty_powertrain",
    "seats_text",
    "seats_count",
    "curb_weight_kg",
    "cargo_capacity_kg",
    "extraction_status",
    "extraction_error",
    "raw_sections_json",
]


def extract_vehicle_lake(
    price_source_index_csv: Path,
    model_source_index_csv: Path,
    output_csv: Path,
    *,
    limit: int | None = None,
    brand: str | None = None,
    archive_only: bool = True,
    max_workers: int = 8,
) -> list[dict[str, str]]:
    with price_source_index_csv.open("r", encoding="utf-8", newline="") as handle:
        price_rows = list(csv.DictReader(handle))
    with model_source_index_csv.open("r", encoding="utf-8", newline="") as handle:
        model_source_rows = list(csv.DictReader(handle))

    supplement_lookup = {
        (row["brand"], row["archive_model_code"]): row for row in model_source_rows
    }

    filtered_rows = []
    for row in price_rows:
        if archive_only and row["source_kind"] != "market_archive_index":
            continue
        if brand and row["brand"] != brand:
            continue
        if not row["price_url"]:
            continue
        filtered_rows.append(row)

    if limit is not None:
        filtered_rows = filtered_rows[:limit]

    LOGGER.info(
        "Vehicle lake extraction start: rows=%s brand=%s archive_only=%s workers=%s",
        len(filtered_rows),
        brand or "all",
        archive_only,
        max_workers,
    )

    output_rows: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_row = {
            executor.submit(build_vehicle_lake_row, row, supplement_lookup): row for row in filtered_rows
        }
        for index, future in enumerate(as_completed(future_to_row), start=1):
            source_row = future_to_row[future]
            try:
                output_rows.append(future.result())
            except Exception as exc:  # pragma: no cover - network/runtime safety
                LOGGER.warning(
                    "Vehicle lake extraction failed: brand=%s model=%s level=%s class=%s year=%s error=%s: %s",
                    source_row["brand"],
                    source_row["model_name"],
                    source_row["level_name"],
                    source_row["class_name"],
                    source_row["year_label"],
                    type(exc).__name__,
                    exc,
                )
                output_rows.append(build_error_vehicle_lake_row(source_row, supplement_lookup, exc))
            if index == 1 or index % 50 == 0 or index == len(filtered_rows):
                current = output_rows[-1]
                LOGGER.info(
                    "Vehicle lake extraction progress: completed=%s/%s current=%s/%s/%s/%s",
                    index,
                    len(filtered_rows),
                    current["brand"],
                    current["model_name"],
                    current["level_name"],
                    current["class_name"],
                )

    output_rows.sort(
        key=lambda row: (
            row["brand"],
            row["model_name"],
            row["level_name"],
            row["class_name"],
            row["year_label"],
        )
    )

    write_rows(output_csv, output_rows, VEHICLE_LAKE_HEADERS)
    LOGGER.info("Vehicle lake extraction complete: output_rows=%s path=%s", len(output_rows), output_csv)
    return output_rows


def build_vehicle_lake_row(
    row: dict[str, str],
    supplement_lookup: dict[tuple[str, str], dict[str, str]],
) -> dict[str, str]:
    html = fetch_html(row["price_url"])
    detail = parse_bobaedream_detail(html)
    supplement = supplement_lookup.get(
        (row["brand"], row["model_code"]),
        {
            "official_price_url": "",
            "official_catalog_url": "",
        },
    )
    return {
        "brand": row["brand"],
        "source_id": row["source_id"],
        "source_kind": row["source_kind"],
        "model_name": row["model_name"],
        "model_code": row["model_code"],
        "level_name": row["level_name"],
        "level_code": row["level_code"],
        "class_name": row["class_name"],
        "class_code": row["class_code"],
        "year_code": row["year_code"],
        "year_label": row["year_label"],
        "primary_source_url": row["price_url"],
        "supplement_official_price_url": supplement.get("official_price_url", ""),
        "supplement_official_catalog_url": supplement.get("official_catalog_url", ""),
        **detail,
    }


def parse_bobaedream_detail(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    section_map: dict[str, dict[str, str]] = {}
    for article_box in soup.select(".article-box"):
        header = article_box.select_one("h3")
        title = normalize_space(header.get_text()) if header else ""
        if not title:
            continue
        section_map[title] = extract_info_items(article_box)

    price_node = soup.select_one(".article-price .price-area span")
    launch_price_text = normalize_space(price_node.get_text()) if price_node else ""
    engine = section_map.get("엔진", {})
    drive = section_map.get("구동", {})
    size = section_map.get("크기/공간", {})
    fuel = section_map.get("연비", {})
    basic_misc = section_map.get("기타", {})
    warranty = section_map.get("보증기간", {})

    body_length, body_width, body_height = parse_dimension_triplet(size.get("차체(길이x너비x높이mm)", ""))

    return {
        "launch_price_text": launch_price_text,
        "launch_price_krw": str(parse_price_to_krw(launch_price_text)),
        "engine_type": decode_value(engine.get("엔진형식", "")),
        "cylinder_count": clean_number(engine.get("실린더수", "")),
        "displacement_cc_text": engine.get("배기량(cc)", ""),
        "displacement_cc": clean_number(engine.get("배기량(cc)", "")),
        "max_output_text": engine.get("최고출력(ps/rpm)", ""),
        "max_output_ps": parse_leading_number(engine.get("최고출력(ps/rpm)", "")),
        "max_torque_text": engine.get("최대토크(kg·m/rpm)", ""),
        "max_torque_kgm": parse_leading_float(engine.get("최대토크(kg·m/rpm)", "")),
        "drive_type": drive.get("구동방식", ""),
        "brake_type": drive.get("브레이크(전/후)", ""),
        "suspension_type": drive.get("서스펜션(전/후)", ""),
        "steering_type": drive.get("스티어링", ""),
        "body_size_text": size.get("차체(길이x너비x높이mm)", ""),
        "body_length_mm": body_length,
        "body_width_mm": body_width,
        "body_height_mm": body_height,
        "wheelbase_mm": clean_number(size.get("측간거리(mm)", "")),
        "fuel_type": fuel.get("연료", ""),
        "combined_efficiency_text": fuel.get("복합연비(km/ℓ)", ""),
        "combined_efficiency_kmpl": parse_leading_float(fuel.get("복합연비(km/ℓ)", "")),
        "city_efficiency_text": fuel.get("도심연비(km/ℓ)", ""),
        "city_efficiency_kmpl": parse_leading_float(fuel.get("도심연비(km/ℓ)", "")),
        "highway_efficiency_text": fuel.get("고속연비(km/ℓ)", ""),
        "highway_efficiency_kmpl": parse_leading_float(fuel.get("고속연비(km/ℓ)", "")),
        "co2_text": fuel.get("CO2배출(g/km)", ""),
        "co2_gkm": clean_number(fuel.get("CO2배출(g/km)", "")),
        "fuel_tank_l": clean_number(fuel.get("연료탱크(ℓ)", "")),
        "warranty_basic": warranty.get("기본", ""),
        "warranty_powertrain": warranty.get("파워트레인", ""),
        "seats_text": basic_misc.get("승차정원", ""),
        "seats_count": parse_leading_number(basic_misc.get("승차정원", "")),
        "curb_weight_kg": clean_number(basic_misc.get("공차중량(kg)", "")),
        "cargo_capacity_kg": clean_number(basic_misc.get("적재용량(kg)", "")),
        "extraction_status": "ok",
        "extraction_error": "",
        "raw_sections_json": json.dumps(section_map, ensure_ascii=False, sort_keys=True),
    }


def build_error_vehicle_lake_row(
    row: dict[str, str],
    supplement_lookup: dict[tuple[str, str], dict[str, str]],
    exc: Exception,
) -> dict[str, str]:
    supplement = supplement_lookup.get(
        (row["brand"], row["model_code"]),
        {
            "official_price_url": "",
            "official_catalog_url": "",
        },
    )
    return {
        "brand": row["brand"],
        "source_id": row["source_id"],
        "source_kind": row["source_kind"],
        "model_name": row["model_name"],
        "model_code": row["model_code"],
        "level_name": row["level_name"],
        "level_code": row["level_code"],
        "class_name": row["class_name"],
        "class_code": row["class_code"],
        "year_code": row["year_code"],
        "year_label": row["year_label"],
        "primary_source_url": row["price_url"],
        "supplement_official_price_url": supplement.get("official_price_url", ""),
        "supplement_official_catalog_url": supplement.get("official_catalog_url", ""),
        "launch_price_text": "",
        "launch_price_krw": "0",
        "engine_type": "",
        "cylinder_count": "",
        "displacement_cc_text": "",
        "displacement_cc": "",
        "max_output_text": "",
        "max_output_ps": "",
        "max_torque_text": "",
        "max_torque_kgm": "",
        "drive_type": "",
        "brake_type": "",
        "suspension_type": "",
        "steering_type": "",
        "body_size_text": "",
        "body_length_mm": "",
        "body_width_mm": "",
        "body_height_mm": "",
        "wheelbase_mm": "",
        "fuel_type": "",
        "combined_efficiency_text": "",
        "combined_efficiency_kmpl": "",
        "city_efficiency_text": "",
        "city_efficiency_kmpl": "",
        "highway_efficiency_text": "",
        "highway_efficiency_kmpl": "",
        "co2_text": "",
        "co2_gkm": "",
        "fuel_tank_l": "",
        "warranty_basic": "",
        "warranty_powertrain": "",
        "seats_text": "",
        "seats_count": "",
        "curb_weight_kg": "",
        "cargo_capacity_kg": "",
        "extraction_status": "error",
        "extraction_error": f"{type(exc).__name__}: {exc}",
        "raw_sections_json": "{}",
    }


def extract_info_items(section: Tag) -> dict[str, str]:
    items: dict[str, str] = {}
    for info_item in section.select(".info-item"):
        title_el = info_item.select_one(".title")
        text_el = info_item.select_one(".text")
        title = normalize_space(title_el.get_text()) if title_el else ""
        text = normalize_space(text_el.get_text()) if text_el else ""
        if title:
            items[title] = text
    return items


def parse_price_to_krw(value: str) -> int:
    match = re.search(r"([\d,]+)\s*만원", value)
    if match:
        return int(match.group(1).replace(",", "")) * 10_000
    return 0


def parse_dimension_triplet(value: str) -> tuple[str, str, str]:
    match = re.search(r"([\d,]+)\s*x\s*([\d,]+)\s*x\s*([\d,]+)", value)
    if not match:
        return "", "", ""
    first, second, third = match.groups()
    return clean_number(first), clean_number(second), clean_number(third)


def clean_number(value: str) -> str:
    match = re.search(r"([\d,]+)", value)
    if not match:
        return ""
    return match.group(1).replace(",", "")


def parse_leading_number(value: str) -> str:
    match = re.search(r"([\d,]+)", value)
    if not match:
        return ""
    return match.group(1).replace(",", "")


def parse_leading_float(value: str) -> str:
    match = re.search(r"([\d,]+(?:\.\d+)?)", value)
    if not match:
        return ""
    return match.group(1).replace(",", "")


def decode_value(value: str) -> str:
    return unquote(value).replace("&", "&")


def write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
