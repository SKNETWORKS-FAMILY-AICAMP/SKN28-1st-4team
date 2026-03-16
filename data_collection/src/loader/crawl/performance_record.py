# pyright: reportMissingImports=false

import asyncio
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from .browser import create_browser_context
from .errors import BlockedRequestError, MissingPerformanceRecordError, SlowResponseError, StaleListingError


async def download_performance_record_pdf(
    detail_url: str,
    output_dir: str | Path,
    *,
    timeout_ms: int = 20_000,
    retry_count: int = 3,
    retry_backoff_seconds: float = 2.0,
    raise_on_blocked_error: bool = False,
    context=None,
) -> Path | None:
    """상세 페이지에서 성능기록부 iframe을 찾아 PDF로 저장한다."""

    if context is None:
        async with create_browser_context() as owned_context:
            return await download_performance_record_pdf(
                detail_url,
                output_dir,
                timeout_ms=timeout_ms,
                retry_count=retry_count,
                retry_backoff_seconds=retry_backoff_seconds,
                raise_on_blocked_error=raise_on_blocked_error,
                context=owned_context,
            )

    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None

    for attempt in range(1, retry_count + 1):
        detail_page = None
        report_page = None
        try:
            detail_page = await context.new_page()
            response = await detail_page.goto(detail_url, wait_until="domcontentloaded", timeout=timeout_ms)
            _raise_for_navigation_response(response, "detail page")
            await detail_page.wait_for_selector("h3", timeout=timeout_ms)
            await detail_page.wait_for_timeout(1_000)

            registration_number = _extract_registration_number(await detail_page.content())
            await _open_performance_record_tab(detail_page, timeout_ms=timeout_ms)
            iframe_src = await _locate_performance_record_iframe(detail_page)
            if not iframe_src:
                raise MissingPerformanceRecordError("performance record iframe missing")

            report_url = _normalize_url(urljoin(detail_page.url, iframe_src))
            output_path = _build_output_path(output_dir_path, registration_number)

            report_page = await context.new_page()
            await report_page.wait_for_timeout(500 * attempt)
            report_response = await report_page.goto(report_url, wait_until="domcontentloaded", timeout=timeout_ms)
            _raise_for_navigation_response(report_response, "performance record")
            await report_page.wait_for_selector("text=중고자동차성능", timeout=timeout_ms)
            await report_page.emulate_media(media="print")
            await report_page.pdf(
                path=str(output_path),
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
                margin={
                    "top": "8mm",
                    "bottom": "8mm",
                    "left": "8mm",
                    "right": "8mm",
                },
            )
            return output_path
        except PlaywrightTimeoutError as exc:
            last_error = SlowResponseError("performance record timeout")
            if attempt == retry_count:
                if raise_on_blocked_error:
                    raise last_error from exc
                return None
        except MissingPerformanceRecordError as exc:
            last_error = exc
            if raise_on_blocked_error:
                raise
            return None
        except (SlowResponseError, StaleListingError) as exc:
            last_error = exc
            if attempt == retry_count:
                if raise_on_blocked_error:
                    raise
                return None
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            error_message = str(exc)
            transient_error = any(
                marker in error_message
                for marker in [
                    "ERR_CONNECTION_CLOSED",
                    "ERR_CONNECTION_RESET",
                    "ERR_NETWORK_CHANGED",
                    "ERR_HTTP2_PROTOCOL_ERROR",
                ]
            )
            if not transient_error or attempt == retry_count:
                if raise_on_blocked_error and transient_error:
                    raise BlockedRequestError(error_message) from exc
                return None
        finally:
            if report_page is not None and not report_page.is_closed():
                await report_page.close()
            if detail_page is not None and not detail_page.is_closed():
                await detail_page.close()

        await asyncio.sleep(retry_backoff_seconds * attempt)

    if raise_on_blocked_error and last_error is not None:
        raise last_error
    return None


async def _open_performance_record_tab(detail_page, *, timeout_ms: int) -> None:
    """성능점검기록부 탭이 있으면 먼저 열어서 iframe이 보이도록 만든다."""

    tab_locator = detail_page.locator('a[href="#3"]')
    if await tab_locator.count() > 0:
        await tab_locator.first.click(force=True, timeout=timeout_ms)
        await detail_page.wait_for_timeout(500)


async def _locate_performance_record_iframe(detail_page) -> str | None:
    """현재 페이지에 존재하는 iframe 중 실제 성능기록부로 보이는 후보를 고른다.

    기준:
    - `src`가 있어야 함
    - 보이는 iframe을 우선함
    - 여러 개면 화면 면적이 가장 큰 iframe을 선택함
    """

    return await detail_page.evaluate(
        """
        () => {
          const candidates = [...document.querySelectorAll('iframe')]
            .map((frame) => {
              const rect = frame.getBoundingClientRect();
              return {
                src: frame.getAttribute('src') || '',
                area: rect.width * rect.height,
                visible: !!(frame.offsetWidth || frame.offsetHeight || frame.getClientRects().length),
              };
            })
            .filter((frame) => frame.src);

          const visible = candidates.filter((frame) => frame.visible);
          const pool = visible.length ? visible : candidates;
          if (!pool.length) {
            return null;
          }

          pool.sort((left, right) => right.area - left.area);
          return pool[0].src;
        }
        """
    )


def _extract_registration_number(html: str) -> str | None:
    """상세 페이지 HTML에서 차량번호를 추출해 PDF 파일명에 사용한다."""

    soup = BeautifulSoup(html, "html.parser")
    for row in soup.select("tr"):
        row_text = " ".join(
            text for text in (_collapse_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])) if text
        )
        if "차량번호" in row_text:
            return _search(r"차량번호\s*:?\s*([0-9가-힣]+)", row_text)
    return None


def _build_output_path(output_dir: Path, registration_number: str | None) -> Path:
    """출력 디렉터리 아래에 충돌 없는 PDF 경로를 만든다."""

    stem = _sanitize_filename(registration_number or "performance_record")
    candidate = output_dir / f"{stem}.pdf"
    if not candidate.exists():
        return candidate

    counter = 2
    while True:
        candidate = output_dir / f"{stem}__{counter}.pdf"
        if not candidate.exists():
            return candidate
        counter += 1


def _sanitize_filename(value: str) -> str:
    """파일명에 쓸 수 없는 문자를 제거한다."""

    import re

    sanitized = re.sub(r"[\\/:*?\"<>|]", "_", value).strip().replace(" ", "")
    return sanitized or "performance_record"


def _normalize_url(url: str) -> str:
    """iframe src를 Playwright가 안정적으로 열 수 있는 URL로 정규화한다."""

    split = urlsplit(url)
    path = quote(split.path, safe="/%")
    query = urlencode(parse_qsl(split.query, keep_blank_values=True), doseq=True)
    return urlunsplit((split.scheme, split.netloc, path, query, split.fragment))


def _collapse_text(value: str | None) -> str | None:
    """공백이 많은 텍스트를 한 줄로 정리한다."""

    if value is None:
        return None
    collapsed = " ".join(value.split())
    return collapsed or None


def _search(pattern: str, text: str) -> str | None:
    """텍스트에서 필요한 값만 정규식으로 추출한다."""

    import re

    match = re.search(pattern, text)
    if not match:
        return None
    return _collapse_text(match.group(1))


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
