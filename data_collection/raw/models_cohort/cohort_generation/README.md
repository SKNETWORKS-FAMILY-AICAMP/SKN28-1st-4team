# Cohort Generation

이 디렉토리는 `original_source/`에서 만든 raw lake를 받아서,
최종적으로 `코호트 생성용 변환 함수`와 `참조 테이블`을 만드는 단계다.

지금부터 이 디렉토리에서 하는 일은 크게 세 가지다.

1. raw lake를 cohort 입력용으로 필터링한다.
2. `brand + model_name` 기준으로 차종 대분류를 붙이는 매핑 테이블을 만든다.
3. `brand + model_name + class_name` 기준으로 체급 점수를 계산하는 함수를 준비한다.

중요한 점은, 여기서는 더 이상 원천 수집을 하지 않는다는 것이다.
이 디렉토리는 `수집된 데이터 -> 코호트용 구조`로 바꾸는 역할만 한다.

## 현재 디렉토리 구성

- `data.bak/`
  - `original_source/data/` 백업본
  - cohort 작업 중 원본을 잃지 않기 위한 보존 디렉토리
- `data/`
  - cohort 단계에서 실제로 사용하는 working output 디렉토리
- `lake_data_filtering.ipynb`
  - raw lake를 읽고, 2010년 이하 모델 제거, 핵심 컬럼 선택, null 점검 등을 수행
- `model_group_manual.ipynb`
  - `brand + model_name` 기준 수동 분류와 category mapping notebook
- `brand_model_trim_reference.ipynb`
  - `brand -> model -> trim_names` JSON reference 생성 notebook
- `cohort_mapping/`
  - notebook에서 불러다 쓰는 경량 category mapping 패키지

## 현재 `data/` 산출물 의미

- `cohort_grouping_input.csv`
  - 코호트 계산 직전의 핵심 입력 테이블
  - 현재는 아래 컬럼만 유지한다.
    - `brand`
    - `model_name`
    - `level_name`
    - `class_name`
    - `launch_price_krw`
    - `displacement_cc`
    - `body_length_mm`
    - `body_width_mm`
    - `body_height_mm`
- `model_inventory.csv`
  - `brand + model_name` 단위 인벤토리
  - 사람이 모델 그룹을 검토하거나 모델 이미지를 정리할 때 쓰는 표
- `model_category_mapping_requests.csv`
  - `brand + model_name` unique request table
  - category mapping agent에 넣는 입력 테이블
- `brand_model_trim_reference.json`
  - 비즈니스 로직에서 LLM에게 넘길 참조 JSON
  - 구조는 `brand -> model_name -> trim_names`

## 현재 합의된 설계 원칙

### 1. category 매핑은 `brand + model_name` 기준

trim이 달라도 차체는 기본적으로 같다고 보고,
차량 대분류(category)는 `brand + model_name` 단위로만 붙인다.

즉:

- `brand + model_name` -> `major_category`

구조로 매핑한다.

`class_name`, `level_name`은 body category를 결정하는 primary key가 아니라,
agent가 참고하는 example/context로만 사용한다.

### 2. 체급 점수는 `brand + model_name + class_name` 기준으로 계산 준비

반면 체급 점수는 trim/class에 따라 달라질 수 있다.
배기량, 출시가격, 차체 크기 차이가 실제로 있기 때문이다.

그래서 category는 모델 단위로 붙이되,
체급 점수는 아래 composite key를 기본 단위로 보는 쪽이 맞다.

- `brand + model_name + class_name`

필요하면 `level_name`도 추가 보조 키로 사용할 수 있지만,
현재 계획은 우선 `class_name`까지 포함한 단위로 시작한다.

### 3. year는 코호트 본체가 아니라 filtering / QA 용도

`year_label`은 sparse 문제를 다시 만들기 때문에
코호트 정의의 핵심 feature에서는 제외한다.

대신 다음 용도로만 사용한다.

- `2010년 이하 모델 제거`
- 연식 없는 모델 제거
- QA / coverage 확인

## 앞으로의 작업 단계

### Stage A. Lake Filtering

담당 notebook:

- `lake_data_filtering.ipynb`

역할:

- raw lake에서 cohort 입력에 필요한 컬럼만 남긴다.
- 2010년 이하 모델과 연식 record가 아예 없는 모델을 제거한다.
- `cohort_grouping_input.csv`를 만든다.

### Stage B. Model Category Mapping

담당 notebook:

- `model_group_manual.ipynb`

역할:

- `brand + model_name` 기준 request table 생성
- category mapping agent 호출
- `major_category` 매핑 테이블 생성
- 나중에 `cohort_grouping_input.csv`에 join

여기서 최종적으로 원하는 매핑 테이블은:

- `brand`
- `model_name`
- `major_category`

정도면 충분하다.

### Stage C. Body/Displacement Based Size Scoring

예정 작업:

- 새 notebook 또는 함수 모듈 추가

역할:

- `brand + model_name + class_name` 기준으로 numeric feature를 집계
- body size와 배기량을 조합해서 체급 점수 함수 설계
- 결과적으로 다음을 반환하는 테이블 또는 함수를 만든다.

예상 출력:

- `brand`
- `model_name`
- `class_name`
- `major_category`
- `size_score`
- `size_band`

## 체급 점수 함수 설계 방향

현재 아이디어는 아래와 같다.

1. body size를 먼저 수치화한다.
   - 기본 후보: `length * width * height`
2. 배기량(`displacement_cc`)을 같이 본다.
3. 둘을 가중 합쳐서 하나의 linear score를 만든다.
4. 같은 `major_category` 안에서 normalize한다.

즉,

- 해치백 안에서의 체급 점수
- SUV 안에서의 체급 점수

처럼 category별로 따로 normalize해야 한다.

여기서 중요한 건,
이 함수는 아직 notebook에서 실험해보고 나서 패키지 함수로 굳히는 게 맞다는 점이다.

## 정리된 목표

최종적으로 이 디렉토리에서 만들고 싶은 것은 아래 두 축이다.

1. `brand + model_name` -> `major_category`
2. `brand + model_name + class_name` -> `size_score`

그리고 이 둘을 조합해서,
주어진 차량이 어떤 코호트에 속하고 같은 category 안에서 어느 정도 체급을 가지는지를
바로 계산할 수 있는 함수로 넘기는 것이 목표다.

즉 지금 이 디렉토리는 `코호트 생성 함수`를 만들기 위한 실험/정리 단계라고 보면 된다.
