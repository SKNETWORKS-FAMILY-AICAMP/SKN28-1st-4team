# pyright: reportMissingImports=false

from dataclasses import asdict, dataclass

from bs4 import BeautifulSoup
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from .browser import create_browser_context
from .errors import BlockedRequestError, SlowResponseError, StaleListingError


@dataclass(slots=True)
class DetailPage:
    """카쿠 상세 페이지에서 보이는 기본 차량 정보를 담는 결과 객체."""

    title: str | None = None
    price_text: str | None = None
    price_manwon: int | None = None
    registration_number: str | None = None
    model_year_text: str | None = None
    first_registration_text: str | None = None
    fuel_type: str | None = None
    transmission: str | None = None
    color: str | None = None
    mileage_text: str | None = None
    mileage_km: int | None = None
    vin: str | None = None
    performance_number: str | None = None
    seller_name: str | None = None
    seller_phone: str | None = None
    dealer_name: str | None = None
    dealer_phone: str | None = None
    dealer_address: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


async def crawl_detail_page(detail_url: str, *, timeout_ms: int = 30_000, context=None) -> DetailPage:
    """실제 상세 페이지를 열고, 화면에 보이는 기본 차량 정보를 추출한다."""

    html = await _load_detail_page_html(detail_url, timeout_ms=timeout_ms, context=context)
    return _parse_detail_page_html(html)


async def _load_detail_page_html(detail_url: str, *, timeout_ms: int, context=None) -> str:
    """Playwright로 실제 페이지를 렌더링한 뒤 최종 HTML을 반환한다."""

    if context is None:
        async with create_browser_context() as owned_context:
            return await _load_detail_page_html(detail_url, timeout_ms=timeout_ms, context=owned_context)

    page = await context.new_page()
    try:
        response = await page.goto(detail_url, wait_until="domcontentloaded", timeout=timeout_ms)
        _raise_for_navigation_response(response, "detail page")
        await page.wait_for_selector("h3", timeout=timeout_ms)
        await page.wait_for_timeout(1_000)
        return await page.content()
    except PlaywrightTimeoutError as exc:
        raise SlowResponseError("detail page timeout") from exc
    finally:
        await page.close()


def _raise_for_navigation_response(response, purpose: str) -> None:
    if response is None:
        return

    status = response.status
    if status in {404, 410}:
        raise StaleListingError(f"{purpose} stale status {status}")
    if status in {401, 403, 429}:
        raise BlockedRequestError(f"{purpose} blocked status {status}")
    if status >= 500:
        raise SlowResponseError(f"{purpose} server status {status}")


def _parse_detail_page_html(html: str) -> DetailPage:
    """렌더링이 끝난 상세 페이지 HTML에서 필요한 필드만 추출한다."""

    soup = BeautifulSoup(html, "html.parser")
    heading = soup.select_one("h3")
    detail_page = DetailPage(title=_collapse_text(heading.get_text(" ", strip=True) if heading else None))

    for row in soup.select("tr"):
        cells = [_collapse_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])]
        cells = [cell for cell in cells if cell]
        if not cells:
            continue

        row_text = " ".join(cells)

        if "판매가" in row_text and detail_page.price_text is None:
            detail_page.price_text = _search(r"판매가\s*:?\s*([\d,]+\s*만원)", row_text)
            detail_page.price_manwon = _parse_manwon(detail_page.price_text)
            detail_page.registration_number = _search(r"차량번호\s*:?\s*([0-9가-힣]+)", row_text)

        if cells[:1] == ["년 형 | 등록"] and len(cells) >= 2:
            parts = [part.strip() for part in cells[1].split("|")]
            if parts:
                detail_page.model_year_text = parts[0]
            if len(parts) > 1:
                detail_page.first_registration_text = parts[1]

        if len(cells) >= 4 and cells[0] == "연료" and cells[2] == "변속기":
            detail_page.fuel_type = cells[1]
            detail_page.transmission = cells[3]

        if len(cells) >= 4 and cells[0] == "색상" and cells[2] == "주행거리":
            detail_page.color = cells[1]
            detail_page.mileage_text = cells[3]
            detail_page.mileage_km = _parse_km(detail_page.mileage_text)

        if "차대번호" in row_text and detail_page.vin is None:
            detail_page.vin = _search(r"차대번호\s*([A-Z0-9]+)", row_text)
        if "성능번호" in row_text and detail_page.performance_number is None:
            detail_page.performance_number = _search(r"성능번호\s*(\d+)", row_text)

        if cells[:2] == ["판매자정보", "성명"] and len(cells) >= 3:
            detail_page.seller_name = cells[2]

        if "연락처" in cells and detail_page.seller_phone is None:
            index = cells.index("연락처")
            if index + 1 < len(cells):
                detail_page.seller_phone = cells[index + 1]

        if "상사" in cells and detail_page.dealer_name is None:
            index = cells.index("상사")
            if index + 1 < len(cells):
                dealer_value = cells[index + 1]
                if "|" in dealer_value:
                    dealer_name, dealer_phone = [part.strip() for part in dealer_value.split("|", 1)]
                    detail_page.dealer_name = dealer_name
                    detail_page.dealer_phone = dealer_phone or None
                else:
                    detail_page.dealer_name = dealer_value

        if len(cells) == 1 and detail_page.dealer_name and detail_page.dealer_address is None:
            detail_page.dealer_address = cells[0]

    return detail_page


def _collapse_text(value: str | None) -> str | None:
    """여러 줄/공백을 한 줄 텍스트로 정리한다."""

    if value is None:
        return None
    collapsed = " ".join(value.split())
    return collapsed or None


def _search(pattern: str, text: str) -> str | None:
    """행 텍스트에서 정규식으로 필요한 값만 뽑는다."""

    import re

    match = re.search(pattern, text)
    if not match:
        return None
    return _collapse_text(match.group(1))


def _parse_manwon(value: str | None) -> int | None:
    """`990만원` 같은 문자열을 정수 만원 단위로 변환한다."""

    import re

    if not value:
        return None
    match = re.search(r"([\d,]+)\s*만원", value)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def _parse_km(value: str | None) -> int | None:
    """`90,571km` 같은 문자열을 정수 km 값으로 변환한다."""

    import re

    if not value:
        return None
    match = re.search(r"([\d,]+)\s*[Kk]?[Mm]?", value)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))
