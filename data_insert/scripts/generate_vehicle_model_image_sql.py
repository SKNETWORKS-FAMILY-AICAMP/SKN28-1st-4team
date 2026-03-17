from __future__ import annotations

import argparse
import base64
import unicodedata
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_DIR = PROJECT_ROOT / "data_insert" / "source" / "images"
DEFAULT_OUTPUT_PATH = (
    PROJECT_ROOT / "data_insert" / "sqls" / "images" / "01_insert_vehicle_model_image_data.sql"
)


@dataclass(frozen=True)
class ImageRecord:
    brand_key: str
    model_name: str
    source_filename: str
    mime_type: str
    payload_base64: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
    )
    return parser.parse_args()


def sql_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def detect_mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".jpg" or suffix == ".jpeg":
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    raise ValueError(f"unsupported image extension: {path.name}")


def build_record(path: Path) -> ImageRecord:
    stem = normalize_text(path.stem)
    if "_" not in stem:
        raise ValueError(f"image filename must contain brand delimiter '_': {path.name}")

    brand_key, model_name = stem.split("_", 1)
    payload_base64 = base64.b64encode(path.read_bytes()).decode("ascii")

    return ImageRecord(
        brand_key=brand_key,
        model_name=model_name,
        source_filename=normalize_text(path.name),
        mime_type=detect_mime_type(path),
        payload_base64=payload_base64,
    )


def iter_records(source_dir: Path) -> list[ImageRecord]:
    supported_files = sorted(
        [
            *source_dir.glob("*.jpg"),
            *source_dir.glob("*.jpeg"),
            *source_dir.glob("*.png"),
            *source_dir.glob("*.webp"),
        ],
        key=lambda path: normalize_text(path.name),
    )
    return [build_record(path) for path in supported_files]


def chunked[T](items: list[T], size: int) -> list[list[T]]:
    if size <= 0:
        raise ValueError("batch_size must be greater than 0")
    return [items[index : index + size] for index in range(0, len(items), size)]


def render_insert_statement(records: list[ImageRecord]) -> str:
    header = """
INSERT INTO `vehicle_model_image` (
    `brand_key`,
    `model_name`,
    `source_filename`,
    `mime_type`,
    `image_blob`
)
VALUES
""".strip()

    row_sql: list[str] = []
    for record in records:
        row_sql.append(
            "    ("
            + ", ".join(
                [
                    sql_quote(record.brand_key),
                    sql_quote(record.model_name),
                    sql_quote(record.source_filename),
                    sql_quote(record.mime_type),
                    f"FROM_BASE64('{record.payload_base64}')",
                ]
            )
            + ")"
        )

    return (
        header
        + "\n"
        + ",\n".join(row_sql)
        + "\nON DUPLICATE KEY UPDATE\n"
        + "    `source_filename` = VALUES(`source_filename`),\n"
        + "    `mime_type` = VALUES(`mime_type`),\n"
        + "    `image_blob` = VALUES(`image_blob`),\n"
        + "    `updated_at` = CURRENT_TIMESTAMP;"
    )


def render_sql(records: list[ImageRecord], batch_size: int) -> str:
    statements = [
        "SET NAMES utf8mb4;",
        "",
        "USE `app_db`;",
        "",
        "START TRANSACTION;",
        "",
    ]

    for batch_index, batch in enumerate(chunked(records, batch_size), start=1):
        statements.append(f"-- batch {batch_index}")
        statements.append(render_insert_statement(batch))
        statements.append("")

    statements.append("COMMIT;")
    statements.append("")
    return "\n".join(statements)


def main() -> None:
    args = parse_args()
    records = iter_records(args.source_dir)
    output_path = args.output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_sql(records, args.batch_size), encoding="utf-8")
    print(
        {
            "output_path": str(output_path),
            "image_count": len(records),
            "batch_size": args.batch_size,
        }
    )


if __name__ == "__main__":
    main()
