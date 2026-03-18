# DB 단위 테스트

이 디렉토리는 `be/src/external/db/client.py` 의 단위 테스트 범위를 설명합니다.

## 테스트 범위

실제 DB 없이 `MySQLClient` 의 내부 동작만 검증합니다.

검증 대상:

- `MySQLClient.from_config()` 가 `DatabaseSettings` 를 그대로 유지하는지
- `connect()` 가 기대한 connection kwargs 를 넘기는지
- context manager 성공 시 commit / close 가 수행되는지
- context manager 실패 시 rollback / close 가 수행되는지
- `health_summary()` 가 `available` / `unavailable` 를 올바르게 반환하는지

## 파일

- `test_client.py`

## 실행 방법

```bash
cd be
uv run pytest tests/unit/external/db/test_client.py
```

전체 DB 단위 테스트 범위를 실행하려면:

```bash
cd be
uv run pytest -m unit tests/unit/external/db
```

## 메모

- Docker 컨테이너가 필요하지 않습니다.
- 실제 MySQL 서버가 필요하지 않습니다.
- 테스트 더블을 사용하므로 외부 인프라에 의존하지 않습니다.
