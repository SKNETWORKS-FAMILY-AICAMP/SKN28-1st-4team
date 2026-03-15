# 구현 상세 설명

이 문서는 현재 `crawl` 패키지가 실제로 어떻게 동작하는지, 그리고 왜 지금은 `Playwright + BeautifulSoup` 조합이 `Crawl4AI`보다 더 적합한지 근거를 포함해 설명합니다.

비교 기준 URL은 사용자가 지정한 다음 상세 페이지입니다.

- `https://www.carku.kr/search/car-detail.html?wDemoNo=0361001191`

## 1. 일반 상세 페이지 크롤링이 실제로 어떻게 동작하는가

일반 상세 페이지 크롤링은 다음 두 단계로 이루어집니다.

1. Playwright Async API로 실제 웹페이지를 연다.
2. 렌더링이 끝난 뒤 `page.content()`로 최종 HTML을 가져와 BeautifulSoup로 파싱한다.

즉, 여기서 BeautifulSoup는 “브라우저가 이미 렌더링한 결과 HTML”을 읽는 역할입니다.
단순히 `requests.get()` 같은 식으로 원본 응답만 받아서 파싱하는 구조가 아닙니다.

실제 흐름은 아래와 같습니다.

```python
await page.goto(detail_url, wait_until="domcontentloaded")
await page.wait_for_selector("h3")
await page.wait_for_timeout(1000)
html = await page.content()
soup = BeautifulSoup(html, "html.parser")
```

Async API를 쓰는 이유는 주피터 노트북 커널이 이미 이벤트 루프를 돌리고 있기 때문입니다. Sync API를 쓰면 `It looks like you are using Playwright Sync API inside the asyncio loop` 오류가 발생할 수 있습니다.

이후 BeautifulSoup는 보이는 표(`tr`, `th`, `td`)를 순회하면서 다음과 같은 행 패턴을 기준으로 값을 뽑습니다.

- `판매가 : 990만원 차량번호 : 28다3785`
- `년 형 | 등록 2017년 | 2016.12 최초등록`
- `연료 휘발유 변속기 오토`
- `색상 회색 주행거리 90,571km`
- `차대번호 KNAFK412BHA686028 성능번호 104611`
- `판매자정보 성명 문태양 사원`
- `연락처 010-5524-8577`
- `상사 태양자동차상사 | 054-975-8577`
- `경북 칠곡군 북삼읍 율리`

이 페이지는 기본 차량 정보가 실제로 표 구조 안에 보이기 때문에, 렌더링된 HTML만 확보되면 BeautifulSoup로 충분히 안정적으로 파싱할 수 있습니다.

## 2. BeautifulSoup 방식의 실제 결과

현재 코드로 위 URL을 실행했을 때 나온 실제 결과는 아래와 같습니다.

```json
{
  "title": "[기아] 더 뉴K3 1.6 GDI 트렌디 스타일",
  "price_text": "990만원",
  "price_manwon": 990,
  "registration_number": "28다3785",
  "model_year_text": "2017년",
  "first_registration_text": "2016.12 최초등록",
  "fuel_type": "휘발유",
  "transmission": "오토",
  "color": "회색",
  "mileage_text": "90,571km",
  "mileage_km": 90571,
  "vin": "KNAFK412BHA686028",
  "performance_number": "104611",
  "seller_name": "문태양 사원",
  "seller_phone": "010-5524-8577",
  "dealer_name": "태양자동차상사",
  "dealer_phone": "054-975-8577",
  "dealer_address": "경북 칠곡군 북삼읍 율리"
}
```

이 값들은 페이지에서 눈으로 확인되는 정보와 직접 대응됩니다. 따라서 현재 범위에서는 “파싱 결과가 맞는지”를 검증하기가 쉽습니다.

## 3. Crawl4AI 방식의 실제 결과

같은 URL에 대해 `uv run --with crawl4ai ...` 로 테스트했을 때, Crawl4AI는 성공적으로 페이지를 읽어 왔습니다.

실제 결과 요약:

```json
{
  "success": true,
  "error_message": "",
  "markdown_preview": "### [기아] 더 뉴K3 1.6 GDI 트렌디 스타일 ... 판매가 : 990만원 | 차량번호 : 28다3785 | 사고이력조회 보험료 조회 ...",
  "cleaned_html_preview": "<html> ... <h1><a href=\"/index.html\"><img src=\"/images/logo.jpg\" ...",
  "html_preview": "<!DOCTYPE html><html lang=\"ko\"> ... <title>(사)전국자동차매매사업조합연합회</title> ..."
}
```

실제로 확인된 Markdown 일부는 아래와 같습니다.

```text
### [기아] 더 뉴K3 1.6 GDI 트렌디 스타일
판매가 : 990만원 | 차량번호 : 28다3785 | 사고이력조회 보험료 조회
```

그리고 `cleaned_html_preview`는 대략 아래처럼 시작합니다.

```html
<html>
<head>
  <title>(사)전국자동차매매사업조합연합회</title>
</head>
<body>
  <div>
    <div>
      <div>
        <h1><a href="/index.html"><img src="/images/logo.jpg" ...
```

즉, Crawl4AI도 페이지 자체를 가져오는 데는 성공합니다. 하지만 현재 범위에서는 결과가 “구조화된 필드”가 아니라 Markdown/HTML 형태이므로, 결국 다시 규칙 기반 파싱을 한 번 더 해야 합니다.

## 4. BeautifulSoup vs Crawl4AI 비교

### 4-1. 현재 페이지에서 바로 얻는 결과 형태

`Playwright + BeautifulSoup`

- 이미 구조화된 결과를 바로 얻음
- 필드 단위 검증이 쉬움
- 현재 필요한 값과 직접 연결됨

`Crawl4AI`

- Markdown 또는 cleaned HTML을 얻음
- 사람이 읽기에는 편하지만, 필드 추출은 결국 후처리가 필요함
- 현재 범위에서는 한 단계가 더 늘어남

### 4-2. 왜 현재는 BeautifulSoup 쪽이 더 적합한가

현재 상세 페이지 크롤링의 목표는 “정해진 필드를 정확히 뽑는 것”입니다.

즉, 지금 필요한 것은 아래와 같은 고정 필드입니다.

- 차량명
- 가격
- 차량번호
- 연식/최초등록일
- 연료/변속기
- 색상/주행거리
- 차대번호
- 성능번호
- 판매자/상사 정보

이 경우에는:

1. Playwright로 렌더링 HTML 확보
2. BeautifulSoup로 표 구조 파싱
3. 정규식/행 패턴으로 값 추출

이 흐름이 가장 단순하고, 디버깅과 테스트도 쉽습니다.

반대로 Crawl4AI는 아래 상황에서 더 유리합니다.

- 페이지 구조가 훨씬 다양하고 정형성이 낮을 때
- Markdown화 자체가 필요할 때
- 여러 페이지를 일반화된 규칙으로 폭넓게 크롤링할 때
- 의미 단위 요약/추출이 더 중요할 때

하지만 지금 상세 페이지는 그 경우가 아닙니다.

### 4-3. 현재 결론

현재 상세 페이지 파싱은 `Playwright + BeautifulSoup`를 유지하는 것이 더 적절합니다.

근거:

- 실제 페이지 렌더링 결과를 기반으로 함
- 실제 출력 결과가 정확한 필드 단위로 검증됨
- Crawl4AI도 수집은 가능하지만 현재 목표에는 추가 후처리가 필요함

## 5. 성능기록부 PDF 다운로드가 실제로 어떻게 동작하는가

성능기록부 단계는 일반 상세 페이지 단계와 역할이 다릅니다.

여기서의 목표는 **피처 추출이 아니라 PDF 파일 저장** 입니다.

현재 흐름:

1. 상세 페이지를 연다.
2. `성능점검기록부` 탭을 클릭한다.
3. 현재 DOM 안에 있는 iframe 후보를 찾는다.
4. 그중 실제 성능기록부로 보이는 iframe을 고른다.
5. 해당 iframe 페이지를 별도 탭으로 연다.
6. 브라우저 인쇄 모드(`print`)로 PDF를 저장한다.

### iframe 탐색이 왜 이렇게 되어 있는가

이 단계는 하드코딩된 특정 호스트 문자열만 믿지 않도록 바꿨습니다.

현재 로직은 다음 기준으로 iframe 후보를 고릅니다.

- `src`가 있어야 함
- 실제로 보이는 iframe을 우선함
- 여러 개라면 화면 면적이 가장 큰 iframe을 선택함

즉, “현재 성능기록부 탭을 연 상태에서, 실제 화면에 붙어 있는 iframe 중 가장 그럴듯한 것”을 고르는 방식입니다.

### 왜 `page.pdf()`를 쓰는가

현재 목표는 브라우저 인쇄에 최대한 가까운 방식으로 PDF를 저장하는 것입니다.

그래서 다음 코드를 사용합니다.

```python
await report_page.emulate_media(media="print")
await report_page.pdf(...)
```

이 방식은 스크린샷 저장이 아니라 브라우저의 인쇄용 렌더링 경로를 사용합니다.

## 6. 실패 시 동작

### 일반 상세 페이지

- `h3` 같은 핵심 요소가 뜨지 않으면 Playwright 단계에서 실패합니다.
- 현재 테스트 대상 페이지에서는 정상 동작을 확인했습니다.

### 성능기록부 PDF

- 성능기록부 탭을 열었는데 iframe이 없으면 `None`
- iframe은 찾았지만 인쇄 단계에서 타임아웃이 나면 `None`

즉, 성능기록부 단계는 현재 “없으면 없다고 반환하고, 있으면 PDF 저장”하는 단순한 계약을 따릅니다.

## 7. 현재 패키지가 하는 일과 하지 않는 일

현재 패키지가 하는 일:

1. 일반 상세 페이지 크롤링
2. 성능기록부 PDF 다운로드

현재 패키지가 하지 않는 일:

- 옵션 선택 상태 해석
- 성능기록부를 다시 읽어서 피처로 변환
- 외부 API 연계
- 이후 데이터 정제/피처 엔지니어링
