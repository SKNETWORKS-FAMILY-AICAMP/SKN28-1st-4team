from __future__ import annotations

import argparse
import logging
from dataclasses import asdict
from pathlib import Path

from collect_sources import collect_all, summarize_price_rows
from extract_vehicle_lake import extract_vehicle_lake
from export_source_subsets import export_source_subsets
from model_source_index import build_model_source_index
from parse_price_pdfs import cache_price_texts
from profile_vehicle_lake import profile_vehicle_lake


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "data"
LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect current official and historical archive model indexes plus price-source URLs.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where CSV outputs will be written.",
    )
    parser.add_argument(
        "--cache-price-text",
        action="store_true",
        help="Download a limited set of discovered price PDFs and cache extracted text.",
    )
    parser.add_argument(
        "--max-price-per-brand",
        type=int,
        default=1,
        help="When caching price text, limit the number of PDFs processed per brand.",
    )
    parser.add_argument(
        "--include-archive-price-index",
        action="store_true",
        help="Expand Bobaedream archive sources into model/engine/trim/year price-source URLs.",
    )
    parser.add_argument(
        "--archive-price-model-limit-per-brand",
        type=int,
        default=None,
        help="When archive price expansion is enabled, limit how many historical models per brand are traversed into trim/year URLs.",
    )
    parser.add_argument(
        "--extract-archive-lake",
        action="store_true",
        help="Visit Bobaedream detail pages and build one raw vehicle-lake CSV.",
    )
    parser.add_argument(
        "--archive-lake-limit",
        type=int,
        default=None,
        help="Limit how many Bobaedream detail rows are extracted into the raw lake CSV.",
    )
    parser.add_argument(
        "--archive-lake-brand",
        type=str,
        default=None,
        help="Optionally restrict raw lake extraction to one brand.",
    )
    parser.add_argument(
        "--archive-lake-workers",
        type=int,
        default=8,
        help="Worker count for concurrent Bobaedream detail extraction.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level. Example: INFO, DEBUG.",
    )
    return parser.parse_args()


def configure_logging(log_level: str) -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)
    output_dir: Path = args.output_dir.resolve()
    LOGGER.info("Starting original source pipeline. output_dir=%s", output_dir)
    models, prices, audits = collect_all(
        output_dir,
        include_archive_price_index=args.include_archive_price_index,
        archive_price_model_limit_per_brand=args.archive_price_model_limit_per_brand,
    )

    print(f"source_registry.csv -> {output_dir / 'source_registry.csv'}")
    print(f"model_index.csv -> {output_dir / 'model_index.csv'}")
    print(f"price_source_index.csv -> {output_dir / 'price_source_index.csv'}")
    print(f"crawl_audit.csv -> {output_dir / 'crawl_audit.csv'}")
    print(f"model rows: {len(models)}")
    print(f"price rows: {len(prices)}")
    print(f"audit rows: {len(audits)}")
    print(f"price rows by brand: {summarize_price_rows(prices)}")

    model_source_rows = build_model_source_index(
        output_dir / "model_index.csv",
        output_dir / "price_source_index.csv",
        output_dir / "model_source_index.csv",
    )
    subset_counts = export_source_subsets(
        output_dir / "model_index.csv",
        output_dir / "price_source_index.csv",
        output_dir,
    )
    print(f"model_source_index.csv -> {output_dir / 'model_source_index.csv'}")
    print(f"model source rows: {len(model_source_rows)}")
    print(f"bobaedream_model_index.csv -> {output_dir / 'bobaedream_model_index.csv'}")
    print(f"bobaedream model rows: {subset_counts['bobaedream_model_rows']}")
    print(f"official_model_index.csv -> {output_dir / 'official_model_index.csv'}")
    print(f"official model rows: {subset_counts['official_model_rows']}")

    if args.extract_archive_lake:
        LOGGER.info(
            "Starting archive lake extraction. limit=%s brand=%s workers=%s",
            args.archive_lake_limit,
            args.archive_lake_brand or "all",
            args.archive_lake_workers,
        )
        lake_rows = extract_vehicle_lake(
            output_dir / "price_source_index.csv",
            output_dir / "model_source_index.csv",
            output_dir / "vehicle_lake_raw.csv",
            limit=args.archive_lake_limit,
            brand=args.archive_lake_brand,
            archive_only=True,
            max_workers=args.archive_lake_workers,
        )
        summary = profile_vehicle_lake(output_dir / "vehicle_lake_raw.csv", output_dir)
        print(f"vehicle_lake_raw.csv -> {output_dir / 'vehicle_lake_raw.csv'}")
        print(f"raw vehicle lake rows: {len(lake_rows)}")
        print(f"vehicle_lake_summary.csv -> {output_dir / 'vehicle_lake_summary.csv'}")
        print(f"zero price rows: {summary.get('zero_price_rows', 0)}")
        print(f"vehicle_lake_zero_price_rows.csv -> {output_dir / 'vehicle_lake_zero_price_rows.csv'}")
    LOGGER.info("Original source pipeline finished.")

    if args.cache_price_text:
        extracted_at = audits[-1].collected_at if audits else ""
        text_rows, variant_rows = cache_price_texts(
            [asdict(row) for row in prices],
            output_dir,
            extracted_at=extracted_at,
            max_price_per_brand=args.max_price_per_brand,
        )
        print(f"price_text_index.csv -> {output_dir / 'price_text_index.csv'}")
        print(f"variant_seed_raw.csv -> {output_dir / 'variant_seed_raw.csv'}")
        print(f"cached price texts: {len(text_rows)}")
        print(f"variant seed rows: {len(variant_rows)}")


if __name__ == "__main__":
    main()
