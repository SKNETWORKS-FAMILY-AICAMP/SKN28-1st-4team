import argparse
import csv
import json
from pathlib import Path


DEFAULT_INPUT_PATH = Path(__file__).resolve().parent / "prepared_training.csv"
DEFAULT_OUTPUT_PATH = (
    Path(__file__).resolve().parents[2] / "fe" / "src" / "assets" / "training_color_options.json"
)


def collect_unique_colors(csv_path: Path) -> list[str]:
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        colors = {
            (row.get("color") or "").strip()
            for row in reader
            if (row.get("color") or "").strip()
        }
    return sorted(colors)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export unique color options from prepared_training.csv for frontend assets.",
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    colors = collect_unique_colors(args.input)
    payload = {
        "source_csv": str(args.input),
        "count": len(colors),
        "colors": colors,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"exported {len(colors)} colors -> {args.output}")


if __name__ == "__main__":
    main()
