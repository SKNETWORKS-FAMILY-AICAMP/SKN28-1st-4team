# Predict Engine Host

## 역할

`predict_engine_host`는 ONNX 모델 호스팅 계층입니다. 학습 프로젝트에서 내보낸 모델 파일 경로를 읽고, 현재 호스팅 상태와 런타임 정보를 API로 제공합니다.

## 디렉토리 구성

- `pyproject.toml`: 프로젝트 메타데이터와 의존성 정의
- `.env`: 로컬 실행과 Docker 런타임에서 함께 사용하는 환경변수 파일
- `Dockerfile`: 모델 호스팅 컨테이너 이미지 정의
- `src/app.py`: 실제 FastAPI 소스 코드 엔트리포인트

## Python 버전

- 최소 Python 버전: `3.12`
- Docker 이미지 기준 Python 버전: `3.12`

## 의존성 및 역할

- `fastapi`: 모델 호스팅용 HTTP API 엔드포인트를 구성합니다.
- `uvicorn`: FastAPI 애플리케이션을 실행하는 ASGI 서버입니다.
- `numpy`: 추후 전처리·후처리와 수치 계산에 사용하는 기본 수치 연산 라이브러리입니다.
- `onnx`: ONNX 모델 파일 메타데이터와 포맷을 확인하는 데 사용합니다.
- `onnxruntime`: 사용 가능한 실행 프로바이더 확인과 실제 ONNX 추론 런타임 계층을 담당합니다.

## 로컬 실행

`uv run`에서 `.env`를 직접 주입해서 실행합니다.

```bash
cd predict_engine_host
uv run --env-file .env uvicorn --app-dir src app:app --reload --host 0.0.0.0 --port 8001
```

## Docker 실행

저장소 루트에서 실행합니다.

```bash
docker compose up --build predict-engine-host
```

## 환경변수 설명

- `APP_ENV`: 실행 환경 구분값입니다.
- `SERVICE_NAME`: API 응답에 표시할 서비스 이름입니다.
- `HOST`: Uvicorn 바인드 주소입니다.
- `PORT`: 모델 호스팅 API 포트입니다.
- `MODEL_PATH`: ONNX 모델 파일 경로입니다.
