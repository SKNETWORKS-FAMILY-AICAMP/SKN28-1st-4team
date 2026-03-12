from pathlib import Path


def main() -> None:
    raw_dir = Path("raw")
    cleaned_dir = Path("cleaned")
    raw_dir.mkdir(parents=True, exist_ok=True)
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    print(
        {
            "service": "data_collection",
            "raw_dir": str(raw_dir),
            "cleaned_dir": str(cleaned_dir),
        }
    )


if __name__ == "__main__":
    main()
