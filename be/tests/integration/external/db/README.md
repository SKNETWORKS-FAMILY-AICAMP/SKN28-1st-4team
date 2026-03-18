# DB 통합 테스트

이 디렉토리는 외부 DB 경계에 대한 통합 테스트 범위를 설명합니다.

## 테스트 범위

단위 테스트와 달리 실제 MySQL 컨테이너를 붙여서 아래를 끝단 기준으로 검증합니다.

- `MySQLClient.connect()` 실연결
- 실제 쿼리 실행 가능 여부
- context manager 기반 insert / select / delete 동작
- 초기화 스키마와 seed 데이터 접근 가능 여부

## 파일

- `conftest.py`
- `test_client_connection.py`
- `test_client_queries.py`
- `docker-compose.yml`
- `docker/test-db/Dockerfile`
- `docker/test-db/initdb/01-create-test-schema.sql`

## 테스트 DB 실행

저장소 루트에서 실행:

```bash
docker compose -f docker-compose.yml -f be/tests/integration/external/db/docker-compose.yml up -d --build test_db_docker
```

## 실행 방법

특정 연결 테스트:

```bash
cd be
RUN_DOCKER_DB_TESTS=1 TEST_DB_HOST=127.0.0.1 TEST_DB_PORT=3307 uv run pytest tests/integration/external/db/test_client_connection.py
```

전체 DB 통합 범위:

```bash
cd be
RUN_DOCKER_DB_TESTS=1 TEST_DB_HOST=127.0.0.1 TEST_DB_PORT=3307 uv run pytest -m integration tests/integration/external/db
```

## 메모

- `RUN_DOCKER_DB_TESTS=1` 이 아니면 skip 됩니다.
- 기본 테스트 컨테이너 이름은 `test_db_docker` 입니다.
- seed 데이터에는 `connectivity_check` 확인용 row 가 포함됩니다.

종료 및 정리:

```bash
docker compose -f docker-compose.yml -f be/tests/integration/external/db/docker-compose.yml down -v
```
