# FE

## 역할

`fe`는 이 모노레포의 Streamlit 프런트엔드입니다. 백엔드와 모델 호스팅 API를 연결하는 화면 레이어가 됩니다.

## 디렉토리 구성

- `pyproject.toml`: 프로젝트 메타데이터와 의존성 정의
- `.env`: 로컬 실행과 Docker 런타임에서 함께 사용하는 환경변수 파일
- `Dockerfile`: 프런트엔드 컨테이너 이미지 정의
- `src/app.py`: 실제 Streamlit 소스 코드 엔트리포인트

## Python 버전

- 최소 Python 버전: `3.12`
- Docker 이미지 기준 Python 버전: `3.12`

## 의존성 및 역할

- `streamlit`: 프런트엔드 UI를 구성하고, 설정값과 상태를 시각적으로 확인하는 데 사용합니다.

## 로컬 실행

`uv run`은 `.env` 파일 주입을 직접 지원하므로 별도 Makefile 없이 실행할 수 있습니다.

```bash
cd fe
uv run --env-file .env streamlit run src/app.py
```

## Docker 실행

저장소 루트에서 실행합니다.

```bash
docker compose up --build fe
```

## 환경변수 설명

- `APP_ENV`: 실행 환경 구분값입니다.
- `SERVICE_NAME`: UI에 표시할 서비스 이름입니다.
- `STREAMLIT_SERVER_ADDRESS`: Streamlit 바인드 주소입니다.
- `STREAMLIT_SERVER_PORT`: Streamlit 포트입니다.
- `STREAMLIT_SERVER_HEADLESS`: 헤드리스 실행 여부입니다.
- `STREAMLIT_BROWSER_GATHER_USAGE_STATS`: Streamlit 사용 통계 수집 여부입니다.
