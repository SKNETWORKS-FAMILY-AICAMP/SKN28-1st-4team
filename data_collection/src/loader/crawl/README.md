# 크롤링 패키지

이 패키지는 카쿠 상세 페이지에서 현재 필요한 두 가지 작업만 담당합니다.

현재 범위:

1. 일반 상세 페이지의 기본 차량 정보를 가져오기
2. 성능기록부 iframe을 PDF로 저장하기

현재 범위에서 제외:

- 옵션 선택 상태 추출
- 성능기록부 PDF를 다시 읽어서 피처로 바꾸는 작업
- PDF 파싱
- 이후 피처 엔지니어링

사용자가 준 실제 URL 기준 동작 설명과 비교 결과는 아래 문서에 정리했습니다.

- `IMPLEMENTATION_DETAILS.md`

## 공개 API

두 공개 함수는 모두 `async` 함수입니다.

- 주피터 노트북에서는 `await`로 직접 호출합니다.
- 일반 파이썬 스크립트에서는 `asyncio.run(...)`으로 감싸서 호출합니다.

### `crawl_detail_page(detail_url)`

File: `detail_page.py`

역할:

- Playwright로 실제 상세 페이지를 엽니다.
- 렌더링이 끝난 뒤 최종 HTML을 가져옵니다.
- 보이는 기본 필드를 파싱합니다.

현재 추출 필드:

- `title`
- `price_text`, `price_manwon`
- `registration_number`
- `model_year_text`
- `first_registration_text`
- `fuel_type`
- `transmission`
- `color`
- `mileage_text`, `mileage_km`
- `vin`
- `performance_number`
- `seller_name`, `seller_phone`
- `dealer_name`, `dealer_phone`, `dealer_address`

반환 타입:

- `DetailPage` 데이터클래스

### `download_performance_record_pdf(detail_url, output_dir)`

File: `performance_record.py`

역할:

- Playwright로 실제 상세 페이지를 엽니다.
- DOM에서 `성능점검기록부` 영역으로 이동합니다.
- 실제 페이지 안에 포함된 iframe을 찾습니다.
- iframe 페이지를 열고 PDF로 저장합니다.

반환 타입:

- 성공 시 `Path`
- iframe을 찾지 못했거나 PDF 저장에 실패하면 `None`

중요:

- 이 함수는 PDF 파일만 저장합니다.
- iframe 페이지를 구조화된 피처로 파싱하지 않습니다.

## 설계 메모

두 함수 모두 Playwright를 쓰는 이유:

- 이 페이지는 실제 브라우저 렌더링 결과를 봐야 안정적으로 다룰 수 있습니다.
- 성능기록부는 실제 DOM 안에서 iframe을 찾아야 합니다.
- PDF는 브라우저의 인쇄 동작에 맞춰 저장해야 합니다.

일반 상세 페이지에서 BeautifulSoup를 계속 쓰는 이유:

- Playwright가 `page.content()`로 최종 HTML을 넘겨주면, 필요한 값은 비교적 안정적인 표 행에 들어 있습니다.
- 지금 필요한 것은 정해진 필드를 정확히 뽑는 일이지, 의미 기반 요약이 아닙니다.
- 추출 결과를 눈으로 비교하고 테스트하기 쉽습니다.

현재 상세 페이지 기준 BeautifulSoup와 Crawl4AI 비교:

- 현재는 `Playwright + BeautifulSoup` 쪽이 더 적합합니다.
- 이유와 실제 출력 비교는 `IMPLEMENTATION_DETAILS.md`에 정리했습니다.

## 파일 구성

- `detail_page.py` - 일반 상세 페이지의 기본 필드 추출
- `performance_record.py` - 성능기록부 iframe을 PDF로 저장

## 테스트

`src/tests/crawl` 아래 테스트는 바로 실행 가능한 스크립트입니다.

- `test_detail_page_page1.py`
- `test_performance_record_page1.py`

`data_collection/src`에서 아래처럼 실행합니다:

```bash
uv run python tests/crawl/test_detail_page_page1.py
uv run python tests/crawl/test_performance_record_page1.py
```

두 테스트 모두 아래 실제 URL을 기준으로 동작합니다.

- `https://www.carku.kr/search/car-detail.html?wDemoNo=0361001191`
