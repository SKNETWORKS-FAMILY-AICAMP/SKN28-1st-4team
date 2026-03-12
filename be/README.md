# BE

## 역할

`be`는 이 모노레포의 백엔드 API 서비스입니다. 현재는 상태 확인, 환경 설정 조회, DB 연결 설정 요약을 제공하는 FastAPI 엔트리포인트를 가지고 있고, 이후 프런트엔드·데이터 파이프라인·모델 호스팅 계층을 연결하는 핵심 API 레이어가 됩니다.

## 디렉토리 구성

- `pyproject.toml`: 프로젝트 메타데이터와 의존성 정의
- `.env`: 로컬 실행과 Docker Compose 런타임에서 사용하는 환경변수 파일 (Git 미추적)
- `.env.example`: 백엔드 런타임 환경변수 템플릿
- `certs/`: 외부 DB SSL 접속용 CA 인증서 보관 디렉토리 (`.gitkeep`만 추적)
- `Dockerfile`: 백엔드 컨테이너 이미지 정의
- `src/app.py`: 실제 FastAPI 소스 코드 엔트리포인트
- `src/env/settings.py`: 런타임 설정 모델 정의
- `src/env/__init__.py`: settings singleton 노출 지점
- `src/external/db/client.py`: PyMySQL 기반 DB 클라이언트
- `src/external/db/factory.py`: DB 클라이언트 조합과 DI provider
- `tests/unit/external/db/test_client.py`: DB 클라이언트 단위 테스트
- `tests/unit/external/db/README.md`: DB 단위 테스트 범위와 실행 방법
- `tests/integration/external/db/test_client_connection.py`: 실제 DB 접속 통합 테스트
- `tests/integration/external/db/README.md`: DB 통합 테스트 범위와 실행 방법
- `tests/integration/external/db/docker-compose.yml`: DB 통합 테스트용 Compose override
- `tests/integration/external/db/docker/test-db/Dockerfile`: `test_db_docker` 이미지 정의
- `tests/integration/external/db/docker/test-db/initdb/`: 테스트 스키마 초기화 SQL

## Python 버전

- 최소 Python 버전: `3.12`
- Docker 이미지 기준 Python 버전: `3.12`

## 의존성 및 역할

- `fastapi`: HTTP API 엔드포인트와 JSON 응답 스키마를 구성합니다.
- `pymysql`: MySQL/MariaDB 연결을 위한 순수 Python 드라이버입니다.
- `uvicorn`: FastAPI 애플리케이션을 로컬과 Docker에서 실행하는 ASGI 서버입니다.

## 로컬 실행

`uv run`이 환경파일 주입을 직접 지원하므로 런타임 환경파일을 바로 사용할 수 있습니다.

```bash
cd be
cp .env.example .env
uv run --env-file .env uvicorn --app-dir src app:app --reload --host 0.0.0.0 --port 8000
```

## Docker 실행

저장소 루트에서 실행합니다.

```bash
cp be/.env.example be/.env
docker compose up --build be
```

## 환경변수 설명

- `APP_ENV`: 실행 환경 구분값입니다.
- `SERVICE_NAME`: API 응답에 표시할 서비스 이름입니다.
- `DB_HOST`: MySQL 서버 호스트입니다.
- `DB_PORT`: MySQL 서버 포트입니다.
- `DB_USER`: DB 접속 계정입니다.
- `DB_PASSWORD`: DB 접속 비밀번호입니다.
- `DB_NAME`: 연결할 데이터베이스 이름입니다.
- `DB_CHARSET`: DB 문자셋입니다.
- `DB_CONNECT_TIMEOUT`: 연결 타임아웃 초 단위 값입니다.
- `DB_SSL_CA_PATH`: DB SSL CA PEM 파일 경로입니다. 로컬과 Docker 모두 `certs/<파일명>.pem` 같은 상대경로 사용을 권장합니다.

기본 `DB_HOST=127.0.0.1` 값은 로컬 실행 기준 예시입니다. Docker에서 외부 DB를 붙일 때는 `.env` 값을 실제 DB 주소나 서비스 이름으로 바꿔야 합니다.

## AWS RDS CA 인증서

- AWS RDS 같은 SSL-required DB를 붙일 때는 `be/certs/` 아래에 글로벌 CA PEM 파일을 두고 `DB_SSL_CA_PATH=certs/<파일명>.pem` 으로 설정합니다.
- `be/certs/.gitkeep`만 Git에 포함되고, 실제 `.pem` 파일은 Git에서 제외됩니다.
- Docker 이미지 빌드 시 `certs/` 디렉토리가 `/app/certs`로 복사되므로, 로컬과 컨테이너에서 같은 상대경로를 그대로 사용할 수 있습니다.
- `be/certs/` 아래에 필요한 CA 파일이 없는데 AWS DB에 연결해야 한다면 AWS 문서에서 인증서를 내려받아 이 디렉토리에 넣어야 합니다: <http://docs.aws.amazon.com/ko_kr/AmazonRDS/latest/UserGuide/UsingWithRDS.SSL.html>
- `tests/integration/external/db/...` 에서 사용하는 로컬 Docker 테스트 DB는 SSL CA 파일이 필요하지 않습니다.

## 설정 구조

- 런타임 설정은 `src/env/settings.py`의 `Settings`로 관리합니다.
- 실제 앱에서는 `src/env/__init__.py`의 `settings` singleton만 사용합니다.
- Python/uv 빌드 설정은 별도 env 파일 대신 `be/Dockerfile`의 `ENV`로 고정합니다.
- 애플리케이션 런타임 환경변수는 계속 `be/.env`와 Docker Compose service 환경설정에서 주입합니다.
- DB 연결 정보는 `src/env/settings.py`의 `DatabaseSettings`로 분리되고, `src/external/db/factory.py`가 이를 주입해 `MySQLClient`를 생성합니다.

## 테스트

테스트는 스코프와 컴포넌트 기준으로 분리합니다.

- `tests/unit/...`: 외부 인프라 없이 컴포넌트 동작만 검증하는 테스트
- `tests/integration/...`: Docker 등 실제 경계를 붙여 검증하는 테스트
- `tests/unit/external/db/...`: DB 클라이언트 단위 테스트
- `tests/integration/external/db/...`: DB 연결 통합 테스트와 해당 테스트 전용 Docker 자산

```bash
cd be
uv run pytest tests/unit/external/db/test_client.py
```

실제 MySQL 연결까지 확인하려면 저장소 루트에서 `test_db_docker` 컨테이너를 먼저 올립니다.

```bash
docker compose -f docker-compose.yml -f be/tests/integration/external/db/docker-compose.yml up -d --build test_db_docker
cd be
RUN_DOCKER_DB_TESTS=1 TEST_DB_HOST=127.0.0.1 TEST_DB_PORT=3307 uv run pytest tests/integration/external/db/test_client_connection.py
```

백엔드 컨테이너도 같은 테스트 DB에 붙여서 확인할 수 있습니다. 이때 `/health` 응답의 `db.status`가 `available`이면 실제 연결이 성공한 상태입니다.

```bash
docker compose -f docker-compose.yml -f be/tests/integration/external/db/docker-compose.yml up --build be test_db_docker
```
