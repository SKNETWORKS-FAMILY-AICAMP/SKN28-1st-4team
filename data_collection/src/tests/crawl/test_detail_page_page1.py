"""Smoke test for normal detail-page crawling using the reference listing URL."""

import asyncio
import json
import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[2]
DETAIL_URL = "https://www.carku.kr/search/car-detail.html?wDemoNo=0361001191"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from loader import crawl_detail_page  # noqa: E402


async def main() -> None:
    detail_page = await crawl_detail_page(DETAIL_URL)

    assert detail_page.title == "[기아] 더 뉴K3 1.6 GDI 트렌디 스타일"
    assert detail_page.price_text == "990만원"
    assert detail_page.price_manwon == 990
    assert detail_page.registration_number == "28다3785"
    assert detail_page.model_year_text == "2017년"
    assert detail_page.first_registration_text == "2016.12 최초등록"
    assert detail_page.fuel_type == "휘발유"
    assert detail_page.transmission == "오토"
    assert detail_page.color == "회색"
    assert detail_page.mileage_text == "90,571km"
    assert detail_page.mileage_km == 90571
    assert detail_page.vin == "KNAFK412BHA686028"
    assert detail_page.performance_number == "104611"
    assert detail_page.seller_name == "문태양 사원"
    assert detail_page.seller_phone == "010-5524-8577"
    assert detail_page.dealer_name == "태양자동차상사"
    assert detail_page.dealer_phone == "054-975-8577"
    assert detail_page.dealer_address == "경북 칠곡군 북삼읍 율리"

    print(json.dumps(detail_page.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
