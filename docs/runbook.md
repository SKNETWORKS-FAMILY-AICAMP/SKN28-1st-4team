---
title: 실행 가이드
---

# 실행 가이드

## 사전 준비

- Python `3.14` 권장
- `uv` 설치
- Docker / Docker Compose 설치
- 외부 DB 접속 정보 준비
- ONNX 모델 파일 준비

## 환경변수 준비

실제 `.env` 파일은 Git에 커밋하지 않는다. 샘플 파일을 복사해서 각 서비스별로 채운다.

```bash
cp be/.env.sample be/.env
cp fe/.env.sample fe/.env
cp predict_engine_host/.env.sample predict_engine_host/.env
```

### 백엔드

`be/.env` 에서는 아래 값이 가장 중요하다.

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`

### 모델 호스팅

`predict_engine_host/.env` 에서는 아래 값이 중요하다.

- `MODEL_PATH`
- `GRPC_PORT`
- `MODEL_FEATURE_NAMES` (필요 시)
- `MODEL_OUTPUT_NAMES` (필요 시)

## 루트 워크스페이스 동기화

```bash
uv sync --all-packages
```

## 가장 쉬운 실행: 루트 Compose

이 프로젝트의 기본 실행 진입점은 루트 `docker-compose.yml` 이다.

```bash
docker compose up --build
```

백그라운드 실행:

```bash
docker compose up -d --build
```

### 올라오는 서비스

- `fe`: `http://localhost:8501`
- `be`: `http://localhost:8000`
- `predict_engine_host`: `http://localhost:8001`

### 주의사항

- DB는 루트 Compose에 포함되어 있지 않다.
- ONNX 파일이 없으면 모델 서비스 health가 `degraded` 일 수 있다.

## 서비스별 로컬 실행

### 프런트엔드

```bash
cd fe
uv run --env-file .env streamlit run src/app.py
```

### 백엔드

```bash
cd be
uv run --env-file .env uvicorn --app-dir src app:app --reload --host 0.0.0.0 --port 8000
```

### 모델 호스팅

```bash
cd predict_engine_host
uv run --env-file .env uvicorn --app-dir src app:app --reload --host 0.0.0.0 --port 8001
```

### 데이터 수집

```bash
cd data_collection
uv run python src/main.py
```

## 빠른 확인

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8001/health
```

## 테스트용 DB 사용

외부 DB 없이 백엔드 연결 테스트를 확인하려면 integration DB override를 사용할 수 있다.

```bash
docker compose -f docker-compose.yml -f be/tests/integration/external/db/docker-compose.yml up -d --build test_db_docker
cd be
RUN_DOCKER_DB_TESTS=1 TEST_DB_HOST=127.0.0.1 TEST_DB_PORT=3307 uv run pytest tests/integration/external/db/test_client_connection.py
```
