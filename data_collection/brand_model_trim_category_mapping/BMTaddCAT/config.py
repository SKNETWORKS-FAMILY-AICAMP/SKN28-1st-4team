from __future__ import annotations

from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
DEFAULT_MAPPING_TABLE_PATH = PROJECT_DIR / "data" / "model_category_mapping_table.csv"
