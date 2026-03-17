from __future__ import annotations

from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
DEFAULT_INPUT_TABLE_PATH = PACKAGE_DIR / "data" / "cohort_grouping_input.csv"
