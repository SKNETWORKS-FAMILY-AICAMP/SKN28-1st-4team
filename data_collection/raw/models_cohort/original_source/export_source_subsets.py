from __future__ import annotations

import csv
from pathlib import Path


def export_source_subsets(
    model_index_csv: Path,
    price_source_index_csv: Path,
    output_dir: Path,
) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)

    with model_index_csv.open("r", encoding="utf-8", newline="") as handle:
        model_rows = list(csv.DictReader(handle))
    with price_source_index_csv.open("r", encoding="utf-8", newline="") as handle:
        price_rows = list(csv.DictReader(handle))

    archive_model_rows = [row for row in model_rows if is_bobaedream_row(row)]
    official_model_rows = [row for row in model_rows if is_official_row(row)]
    archive_price_rows = [row for row in price_rows if is_bobaedream_row(row)]
    official_price_rows = [row for row in price_rows if is_official_row(row)]

    write_rows(output_dir / "bobaedream_model_index.csv", archive_model_rows)
    write_rows(output_dir / "official_model_index.csv", official_model_rows)
    write_rows(output_dir / "bobaedream_price_source_index.csv", archive_price_rows)
    write_rows(output_dir / "official_price_source_index.csv", official_price_rows)

    return {
        "bobaedream_model_rows": len(archive_model_rows),
        "official_model_rows": len(official_model_rows),
        "bobaedream_price_rows": len(archive_price_rows),
        "official_price_rows": len(official_price_rows),
    }


def is_bobaedream_row(row: dict[str, str]) -> bool:
    return "bobaedream" in row.get("source_id", "")


def is_official_row(row: dict[str, str]) -> bool:
    return row.get("source_kind") == "official_catalog_index"


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
