# Original Source

이 디렉토리는 `models_cohort` 작업의 1단계인 `원천 데이터 수집`만 담당한다.

핵심 목표는 다음 두 가지다.

1. `보배드림`을 메인 소스로 사용해 과거/현재 모델의 상세 페이지 URL을 최대한 많이 확보한다.
2. 확보한 상세 페이지에서 `출시가격`, `트림`, `배기량`, `연료`, `구동방식`, `차체 크기` 같은 값을 추출해 하나의 raw data lake CSV로 만든다.

여기서는 아직 cohort를 계산하지 않는다.
여기서 하는 일은 `어디서 가져올지 정리 -> 어떤 URL을 방문할지 정리 -> 실제 raw row를 추출`하는 것까지다.

## 소스 역할

현재 이 디렉토리에서 다루는 원천 소스는 두 종류다.

- `보배드림`: 메인 소스
  - 과거 모델이 많다.
  - 모델 -> 세부모델(level) -> 트림(class) -> 연식(year) 구조를 제공한다.
  - 상세 페이지에 `출시가격`, `배기량(cc)`, `연비`, `구동방식`, `차체 크기` 등이 들어있다.
- `공식 사이트`: 보조 소스
  - 현재 판매 모델 위주다.
  - 보배드림에서 최근 모델을 공식 모델과 연결할 때 사용한다.
  - 가격표 PDF, 카탈로그 PDF 링크를 supplement metadata로 붙인다.

즉, 현재 설계는 아래처럼 이해하면 된다.

- `보배드림 = primary source`
- `공식 사이트 = supplementary source`

## 이 디렉토리에서 만드는 파일

모든 결과물은 `data/` 아래에 생성된다.

### 1) 원천 소스 목록

- `source_registry.csv`
  - 어떤 브랜드를 어떤 소스로 수집하는지 정의한 레지스트리

### 2) 모델 단위 인덱스

- `model_index.csv`
  - 전체 모델 인덱스
  - 공식 사이트 모델 + 보배드림 archive 모델이 같이 들어간다.
- `bobaedream_model_index.csv`
  - 보배드림 모델만 따로 분리한 파일
- `official_model_index.csv`
  - 공식 사이트 모델만 따로 분리한 파일

이 단계의 1행은 `모델 1개`를 뜻한다.

### 3) 상세 페이지 URL 인덱스

- `price_source_index.csv`
  - 전체 상세 페이지 URL 인덱스
- `bobaedream_price_source_index.csv`
  - 보배드림 상세 페이지 URL만 따로 분리한 파일
- `official_price_source_index.csv`
  - 공식 사이트 가격표/카탈로그 링크만 따로 분리한 파일

이 단계의 1행은 단순한 모델 1개가 아니다.
보통 아래 조합 1개를 의미한다.

- `모델`
- `세부모델(level)`
- `트림(class)`
- `연식(year)`

그래서 `price_rows` 수가 모델 수보다 훨씬 크게 나온다.

### 4) 모델-소스 연결 테이블

- `model_source_index.csv`
  - 보배드림 archive 모델을 기준으로,
  - 연결 가능한 공식 사이트 모델/가격표/카탈로그 링크를 보조 정보로 붙인 파일

이 파일은 나중에 최근 모델 보강이나 누락값 보완에 사용한다.

### 5) Raw data lake

- `vehicle_lake_raw.csv`
  - 실제 보배드림 상세 페이지를 방문해서 추출한 raw row 모음
  - 이 디렉토리의 가장 중요한 산출물

현재 여기에는 예를 들어 다음 값들이 들어간다.

- 브랜드
- 모델명
- 세부모델명
- 트림명
- 연식
- 출시가격
- 배기량
- 연료
- 구동방식
- 최고출력
- 최대토크
- 차체 길이/너비/높이
- 휠베이스
- 승차정원
- 연비
- 보증기간
- 원본 section JSON

### 6) Raw lake 요약/점검 파일

- `vehicle_lake_summary.csv`
  - raw lake 전체 요약
  - 총 row 수, 가격 0 row 수, extraction error row 수 등
- `vehicle_lake_zero_price_rows.csv`
  - `launch_price_krw = 0` 인 row만 따로 모은 파일

이 파일은 `출시가격 누락/대체 전략`을 나중에 세울 때 먼저 확인하는 용도다.

### 7) 실험용 파일

- `price_text_index.csv`
- `variant_seed_raw.csv`

이 둘은 공식 사이트 PDF 파싱 실험용이다.
현재 메인 경로는 아니고, 보조 실험 결과물로 보면 된다.

## 코드 파일 역할

- `source_registry.py`
  - 브랜드별 수집 레지스트리 정의
- `collect_sources.py`
  - 모델 인덱스와 상세 페이지 URL 인덱스 생성
- `export_source_subsets.py`
  - 전체 인덱스를 보배드림/공식 사이트 파일로 분리 저장
- `model_source_index.py`
  - 보배드림 모델과 공식 모델을 연결
- `extract_vehicle_lake.py`
  - 보배드림 상세 페이지에서 실제 raw row를 추출
- `profile_vehicle_lake.py`
  - raw lake를 요약하고 가격 0 row를 따로 분리
- `run.py`
  - 위 전체 파이프라인 실행 entry point

## 실행 위치

반드시 `data_collection/` 디렉토리에서 실행하는 것을 권장한다.

```bash
cd /Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/data_collection
```

## 실행 예시

### 1) 모델/URL 인덱스만 생성

```bash
uv run python raw/models_cohort/original_source/run.py \
  --include-archive-price-index \
  --log-level INFO
```

### 2) 일부만 테스트하면서 raw lake까지 생성

```bash
uv run python raw/models_cohort/original_source/run.py \
  --include-archive-price-index \
  --archive-price-model-limit-per-brand 1 \
  --extract-archive-lake \
  --archive-lake-limit 5 \
  --archive-lake-workers 2 \
  --log-level INFO
```

### 3) 전체 실행

```bash
uv run python raw/models_cohort/original_source/run.py \
  --include-archive-price-index \
  --extract-archive-lake \
  --archive-lake-workers 8 \
  --log-level INFO
```

## 로그 해석

로그에 나오는 `price_rows`는 `모델 수`가 아니다.

예를 들어 아래 구조가 있으면:

- 모델 1개
- 세부모델 3개
- 트림 4개
- 연식 2개

실제로는 `3 x 4 x 2 = 24 rows`가 생길 수 있다.

즉 로그의 `price_rows_total`은 `상세 페이지 URL row 누적 개수`라고 이해하면 된다.

## 이 디렉토리의 역할 정리

이 디렉토리는 다음 질문에 답하기 위해 존재한다.

- 어떤 모델이 있는가?
- 각 모델의 상세 데이터는 어느 URL에서 가져오는가?
- 각 상세 페이지에서 어떤 값을 추출할 수 있는가?
- 그것을 raw lake로 어떻게 쌓는가?

그 다음 단계인 `cohort_generation/`에서는,
여기서 만든 `vehicle_lake_raw.csv`를 바탕으로 cohort 계산에 쓸 입력 테이블을 만든다.
