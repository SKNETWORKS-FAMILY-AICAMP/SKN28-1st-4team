from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


SUMMARY_HEADERS = ["metric", "value"]


def profile_vehicle_lake(source_csv: Path, output_dir: Path) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if not source_csv.exists():
        write_rows(output_dir / "vehicle_lake_summary.csv", [], SUMMARY_HEADERS)
        write_rows(output_dir / "vehicle_lake_zero_price_rows.csv", [], [])
        return {}

    with source_csv.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    zero_rows = [row for row in rows if int(row.get("launch_price_krw") or "0") <= 0]
    nonzero_rows = [row for row in rows if int(row.get("launch_price_krw") or "0") > 0]
    with_displacement = [row for row in rows if row.get("displacement_cc")]
    with_drive_type = [row for row in rows if row.get("drive_type")]
    error_rows = [row for row in rows if row.get("extraction_status") == "error"]

    summary = {
        "total_rows": len(rows),
        "zero_price_rows": len(zero_rows),
        "nonzero_price_rows": len(nonzero_rows),
        "extraction_error_rows": len(error_rows),
        "rows_with_displacement": len(with_displacement),
        "rows_with_drive_type": len(with_drive_type),
    }

    zero_by_brand = Counter(row["brand"] for row in zero_rows)
    for brand, count in sorted(zero_by_brand.items()):
        summary[f"zero_price_rows_{brand}"] = count

    write_rows(
        output_dir / "vehicle_lake_summary.csv",
        [{"metric": key, "value": str(value)} for key, value in summary.items()],
        SUMMARY_HEADERS,
    )
    write_rows(
        output_dir / "vehicle_lake_zero_price_rows.csv",
        zero_rows,
        list(zero_rows[0].keys()) if zero_rows else [],
    )
    return summary


def write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)
