# Models Cohort

이 디렉토리는 차량 코호트 생성 작업을 한곳에 모아둔 영역입니다.

현재 흐름은 두 단계로 나뉩니다.

1. `original_source/`
   - 국내 제조사 원천 소스 인덱스 수집
   - 보배드림 archive 인덱스 수집
   - 가격/상세 페이지 URL 정리
   - 보배드림 상세 페이지를 주 구조화 소스로 사용
   - 공식 가격표/카탈로그 링크는 보조 소스로 유지
   - 필요 시 PDF 캐시 및 텍스트 추출 실험
   - 최종 raw vehicle lake CSV 생성
2. `cohort_generation/`
   - raw lake 를 코호트 입력 형태로 정리
   - category / size score 계산용 참조 테이블 생성
   - weighted-neighbor cohort 입력 준비

## 현재 범위

현재 v1 범위는 국내 브랜드 위주입니다.

- 현대
- 기아
- 쉐보레
- 르노
- KGM

## 핵심 목표

현재 이 작업에서 가장 중요한 것은 `트림 단위 출시가격 확보` 입니다.  
그래서 원천 수집 단계는 HTML 원문 대량 보관보다 아래 산출물 생성에 집중합니다.

- `price-source URL` 인덱스
- `vehicle_lake_raw.csv`
- 코호트 입력용 seed / reference 테이블

## 하위 디렉토리

- [original_source/README.md](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/data_collection/raw/models_cohort/original_source/README.md)
  - 원천 소스 수집과 raw lake 생성
- [cohort_generation/README.md](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/data_collection/raw/models_cohort/cohort_generation/README.md)
  - 코호트용 입력 정리, category / size score 준비

## 현재 산출물 관점 요약

- 원천 단계 결과:
  - `vehicle_lake_raw.csv`
  - `source_registry.csv`
  - `model_index.csv`
  - `price_source_index.csv`
- 코호트 단계 결과:
  - `cohort_grouping_input.csv`
  - `brand_model_trim_reference.json`
  - category mapping 입력/출력 테이블

## 설계 메모

- 원천 데이터는 최대한 많이 모으되, 실제 모델링/코호트 계산용 구조는 별도 단계에서 정제합니다.
- `brand + model_name` 은 category 매핑의 핵심 키입니다.
- `brand + model_name + class_name` 은 체급 점수 계산의 핵심 키입니다.
- 연식은 코호트 정의의 본체보다는 필터링과 QA 쪽에 가깝게 다룹니다.
