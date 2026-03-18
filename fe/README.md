# FE

`fe` 는 Streamlit 기반 프런트엔드 애플리케이션입니다.  
사용자는 이 앱에서 차량을 선택하고, 주행거리·구매일자·색상 같은 기본 정보를 입력한 뒤 현재 예측가와 향후 감가 흐름을 확인합니다.

## 현재 화면 구성

- 랜딩 페이지
- 차량 입력 페이지
- 결과 페이지

현재 UX 흐름은 아래와 같습니다.

1. 브랜드 선택
2. 모델 검색 및 모델 카드 선택
3. 세부 트림 선택
4. 기본 차량 정보 입력
5. 결과 페이지에서 현재 예측가, 적정 매도 범위, 향후 1~5년 가격 흐름, 상승/하락 요인 확인

## 디렉토리 구조

```text
fe/
├─ README.md
├─ .env.example
├─ .streamlit/
├─ assets/
├─ src/
│  ├─ app.py
│  ├─ assets/
│  ├─ components/
│  ├─ core/
│  ├─ mock_data/
│  ├─ models/
│  ├─ pages/
│  ├─ services/
│  └─ styles/
└─ Dockerfile
```

## 주요 소스 역할

- `src/app.py`
  - 페이지 라우팅과 전체 조합 진입점
- `src/pages/landing`
  - 첫 화면
- `src/pages/entry`
  - 차량 입력 화면
- `src/pages/expect`
  - 예측 결과 화면
- `src/components/vehicle_selector`
  - 브랜드/모델/트림 선택 UI
- `src/components/basic_vehicle_form`
  - 번호판, 구매 일자, 주행거리, 색상 등 기본 입력 UI
- `src/components/input_summary`
  - 가격 예측 실행 버튼과 입력 요약
- `src/components/result_hero`
  - 현재 예측가/적정 매도 범위 영역
- `src/components/price_chart`
  - 현재~5년 후 가격 차트
- `src/components/factor_insights`
  - 상승/하락 요인 카드
- `src/services/query_facade.py`
  - 프런트가 사용하는 단일 질의 진입점
- `src/services/query_helper.py`
  - `httpx` 기반 백엔드 호출
- `src/services/query_mapper.py`
  - form state <-> DTO <-> API payload 변환

## 데이터 소스 원칙

프런트는 아래 두 종류의 데이터를 다르게 다룹니다.

### 1. 로컬 자산으로 직접 쓰는 데이터

- 브랜드/모델/세부 트림 참조
  - `src/assets/brand_model_trim_reference.json`
- 색상 옵션 참조
  - `src/assets/training_color_options.json`

이 데이터는 배포 시점에 같이 포함되는 정적 자산입니다.  
즉, 차량 선택용 카탈로그는 백엔드에서 받지 않습니다.

### 2. 백엔드로 요청하는 데이터

- 모델 카드 이미지
- 가격 예측 결과
- 상승/하락 요인 분석

현재 프런트가 호출하는 API:

- `POST /api/v1/frontend/model-images`
- `POST /api/v1/frontend/price-prediction`
- `POST /api/v1/frontend/price-factors`

## 환경변수

주요 환경변수는 아래와 같습니다.

- `APP_ENV`
- `SERVICE_NAME`
- `STREAMLIT_SERVER_ADDRESS`
- `STREAMLIT_SERVER_PORT`
- `STREAMLIT_SERVER_HEADLESS`
- `STREAMLIT_BROWSER_GATHER_USAGE_STATS`
- `FE_QUERY_BASE_URL`
- `FE_QUERY_MODEL_IMAGE_PAGE_PATH`
- `FE_QUERY_PRICE_PATH`
- `FE_QUERY_PRICE_FACTORS_PATH`
- `FE_QUERY_TIMEOUT_SECONDS`

샘플 파일:

- [fe/.env.example](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/fe/.env.example)

### `FE_QUERY_BASE_URL`

백엔드 호출 기본 주소입니다.

권장값:

- 로컬에서 직접 실행할 때: `http://127.0.0.1:8000`
- Docker Compose 안에서 FE 컨테이너가 BE 컨테이너를 호출할 때: `http://be:8000`

## 로컬 실행

```bash
cd fe
uv run --env-file .env streamlit run src/app.py
```

기본 접속 주소:

- `http://localhost:8501`

## Docker 실행

루트에서 실행:

```bash
docker compose up --build fe
```

## 상태 관리 원칙

- 사용자 입력은 `st.session_state` 를 사용합니다.
- 상태 읽기/정리는 `src/core/state.py` 에 모읍니다.
- 위젯 내부에서 직접 API를 치지 않고, 페이지나 facade를 통해 호출합니다.

## 현재 주의사항

- Streamlit 특성상 검색/초기화/재선택 버튼은 `session_state` callback 기반으로 제어합니다.
- 결과 페이지는 백엔드 응답을 세션 캐시에 보관합니다.
- 모델 카드 이미지는 현재 페이지 9개만 백엔드에 요청합니다.
- 백엔드 이미지가 DB에 없으면 로컬 이미지 fallback 을 사용합니다.
