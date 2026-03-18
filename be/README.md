# BE

`be` 는 FastAPI 기반 백엔드 서비스입니다.  
현재 프런트와 직접 연결되는 차량 예측 API, 요인 분석 API, 모델 이미지 API를 제공합니다.

## 현재 책임 범위

- 서비스 상태 확인
- 프런트 입력 DTO 수신
- `brand/model/trim` 기반 파생 피처 생성
- CatBoost 모델 예측 실행
- 향후 1~5년 감가 시뮬레이션
- 상승/하락 요인 AI 분석
- 모델 이미지 조회

## 디렉토리 구조

```text
be/
├─ README.md
├─ .env.example
├─ certs/
├─ src/
│  ├─ app.py
│  ├─ env/
│  ├─ external/
│  │  ├─ ai_agent/
│  │  ├─ db/
│  │  └─ predict_engine/
│  ├─ observability/
│  ├─ prompts/
│  ├─ services/
│  └─ sql_commands/
└─ tests/
```

## 현재 API

### 상태/엔진 API

- `GET /`
- `GET /health`
- `GET /predict-engine/health`
- `POST /predict-engine/predict`
- `POST /predict-engine/project`

### 프런트 전용 API

- `POST /api/v1/frontend/model-images`
- `POST /api/v1/frontend/price-prediction`
- `POST /api/v1/frontend/price-factors`
- `GET /vehicle-model-image`

## 프런트 예측 플로우

### 1. 모델 이미지

`POST /api/v1/frontend/model-images`

입력:

- `brand_key`
- `brand_label`
- `model_names[]`

역할:

- 현재 페이지에 보이는 모델 카드 목록만 받아 이미지 경로를 반환합니다.
- DB 이미지가 없으면 `data_insert/source/images` 로 fallback 합니다.

### 2. 가격 예측

`POST /api/v1/frontend/price-prediction`

현재 프런트가 보내는 최소 입력:

- `brand_key`
- `brand_label`
- `model_name`
- `trim_name`
- `plate`
- `purchase_date`
- `is_used_purchase`
- `mileage_km`
- `color`
- `transmission`

이 중 실제 모델 feature 생성에 쓰는 값은 아래입니다.

- `brand_key`
- `model_name`
- `trim_name`
- `purchase_date`
- `mileage_km`
- `color`

백엔드는 이 입력으로 아래 파생 피처를 만듭니다.

- `major_category`
- `size_score`
- `vehicle_age_years`

그리고 최종적으로 현재 모델이 쓰는 8개 feature를 구성합니다.

- `brand`
- `model_name`
- `trim_name`
- `major_category`
- `size_score`
- `vehicle_age_years`
- `color`
- `mileage_km`

### 3. 상승/하락 요인 분석

`POST /api/v1/frontend/price-factors`

역할:

- 중고차 가격 맥락의 상승/하락 요인을 자연어로 반환합니다.
- 기본적으로 AI 에이전트를 사용합니다.
- AI 호출 실패 시 heuristic fallback 을 사용합니다.
- 색상 선호, 연간 주행거리 기준, 사용 기간 등을 같이 고려합니다.

프롬프트:

- `src/prompts/frontend_price_factor_instructions.txt`

## 예측 엔진 구성

백엔드는 내부 `external/predict_engine` 패키지를 직접 사용합니다.

주요 자산:

- `src/external/predict_engine/model_assets/model.cbm`
- `src/external/predict_engine/model_assets/feature_manifest.json`
- `src/external/predict_engine/model_assets/metrics.json`

주요 보조 패키지:

- `src/external/predict_engine/bmt_add_cat`
- `src/external/predict_engine/bmt2score`
- `src/external/predict_engine/feature_vectorizer`
- `src/external/predict_engine/model_runtime`

즉 현재 MVP 경로에서는 별도 모델 호스팅 서버 없이 백엔드가 CatBoost 자산을 직접 읽어 예측합니다.

## 설정 파일

주요 설정은 `src/env/settings.py` 에 있습니다.

중요한 환경변수:

- `APP_ENV`
- `SERVICE_NAME`
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `DB_CHARSET`
- `DB_CONNECT_TIMEOUT`
- `DB_SSL_CA_PATH`
- `PREDICT_ENGINE_MODEL_PATH`
- `PREDICT_ENGINE_FEATURE_MANIFEST_PATH`
- `AI_AGENT_API_KEY` 또는 `OPENROUTER_API_KEY`
- `AI_AGENT_MODEL`
- `AI_AGENT_BASE_URL`

## 로컬 실행

```bash
cd be
uv run --env-file .env uvicorn --app-dir src app:app --reload --host 0.0.0.0 --port 8000
```

## Docker 실행

루트에서:

```bash
docker compose up --build be
```

## 테스트

단위/통합 DB 테스트 README:

- [be/tests/unit/external/db/README.md](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/be/tests/unit/external/db/README.md)
- [be/tests/integration/external/db/README.md](/Users/iwonbin/workspace/Study/boot/SKN28-1st-4team/be/tests/integration/external/db/README.md)

## 현재 주의사항

- `.env` 실파일은 Git에 포함하지 않습니다.
- DB 이미지가 없더라도 모델 이미지 API는 로컬 이미지 fallback 을 사용합니다.
- 프런트 전용 projection 은 `FrontendPricePredictionService` 에서 직접 반복 예측합니다.
- `PredictEngineService.project()` 는 일반용 엔진 API 용도로 남아 있습니다.
