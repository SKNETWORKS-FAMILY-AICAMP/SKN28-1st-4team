"""Smoke test for performance-record PDF download using the reference listing URL."""

import asyncio
import sys
import tempfile
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[2]
DETAIL_URL = "https://www.carku.kr/search/car-detail.html?wDemoNo=0361001191"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from loader import download_performance_record_pdf  # noqa: E402


async def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        pdf_path = await download_performance_record_pdf(DETAIL_URL, Path(tmp_dir))
        assert pdf_path is not None, "Expected the performance record iframe to be downloadable."
        assert pdf_path.exists(), "Expected the downloaded performance-record PDF file to exist."
        assert pdf_path.name == "28다3785.pdf"
        assert pdf_path.stat().st_size > 0, "Expected a non-empty PDF file."
        print(pdf_path)


if __name__ == "__main__":
    asyncio.run(main())
