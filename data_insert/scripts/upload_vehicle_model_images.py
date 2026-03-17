from __future__ import annotations

import argparse
import os
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import pymysql
from pymysql.connections import Connection


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BE_DIR = PROJECT_ROOT / "be"
DEFAULT_SOURCE_DIR = PROJECT_ROOT / "data_insert" / "source" / "images"

INSERT_SQL = """
INSERT INTO `vehicle_model_image` (
    `brand_key`,
    `model_name`,
    `source_filename`,
    `mime_type`,
    `image_blob`
) VALUES (%s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    `source_filename` = VALUES(`source_filename`),
    `mime_type` = VALUES(`mime_type`),
    `image_blob` = VALUES(`image_blob`),
    `updated_at` = CURRENT_TIMESTAMP
""".strip()


@dataclass(frozen=True)
class ImageRecord:
    brand_key: str
    model_name: str
    source_filename: str
    mime_type: str
    payload: bytes


@dataclass(frozen=True)
class ConnectionInfo:
    host: str
    port: int
    user: str
    password: str
    database: str
    charset: str
    collation: str
    connect_timeout: int


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def detect_mime_type(payload: bytes, path: Path) -> str:
    if payload.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if payload.startswith(b"RIFF") and payload[8:12] == b"WEBP":
        return "image/webp"
    raise ValueError(f"unsupported image extension: {path.name}")


def build_record(path: Path) -> ImageRecord:
    stem = normalize_text(path.stem)
    if "_" not in stem:
        raise ValueError(f"image filename must contain brand delimiter '_': {path.name}")

    brand_key, model_name = stem.split("_", 1)
    payload = path.read_bytes()
    return ImageRecord(
        brand_key=brand_key,
        model_name=model_name,
        source_filename=normalize_text(path.name),
        mime_type=detect_mime_type(payload, path),
        payload=payload,
    )


def load_records(source_dir: Path, brand: str | None) -> list[ImageRecord]:
    files = sorted(
        [
            *source_dir.glob("*.jpg"),
            *source_dir.glob("*.jpeg"),
            *source_dir.glob("*.png"),
            *source_dir.glob("*.webp"),
        ],
        key=lambda path: normalize_text(path.name),
    )
    records = [build_record(path) for path in files]
    if brand is None:
        return records
    return [record for record in records if record.brand_key == brand]


def resolve_ssl_ca_path(value: str | None) -> str | None:
    if not value:
        return None
    path = Path(value).expanduser()
    if path.is_absolute():
        return str(path)
    return str((BE_DIR / path).resolve())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL") or os.getenv("DB_URL") or None,
    )
    parser.add_argument("--host", default=os.getenv("DB_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("DB_PORT", "3306")))
    parser.add_argument("--user", default=os.getenv("DB_USER", "app_user"))
    parser.add_argument("--password", default=os.getenv("DB_PASSWORD", "app_password"))
    parser.add_argument("--database", default=os.getenv("DB_NAME", "app_db"))
    parser.add_argument("--charset", default=os.getenv("DB_CHARSET", "utf8mb4"))
    parser.add_argument(
        "--collation",
        default=os.getenv("DB_COLLATION", "utf8mb4_unicode_ci"),
    )
    parser.add_argument(
        "--connect-timeout",
        type=int,
        default=int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
    )
    parser.add_argument("--ssl-ca-path", default=os.getenv("DB_SSL_CA_PATH") or None)
    parser.add_argument("--brand", default=None)
    parser.add_argument("--commit-every", type=int, default=20)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check-connection", action="store_true")
    return parser.parse_args()


def resolve_connection_info(args: argparse.Namespace) -> ConnectionInfo:
    if not args.database_url:
        return ConnectionInfo(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            database=args.database,
            charset=args.charset,
            collation=args.collation,
            connect_timeout=args.connect_timeout,
        )

    parsed = urlparse(args.database_url)
    scheme = parsed.scheme.split("+", 1)[0]
    if scheme != "mysql":
        raise ValueError("database_url must use the mysql:// scheme")
    if parsed.hostname is None:
        raise ValueError("database_url must include a hostname")
    if parsed.username is None:
        raise ValueError("database_url must include a username")

    query = parse_qs(parsed.query)
    database_name = unquote(parsed.path.lstrip("/")) or args.database
    charset = query.get("charset", [args.charset])[0]
    collation = query.get("collation", [args.collation])[0]
    connect_timeout_value = query.get("connect_timeout", [str(args.connect_timeout)])[0]

    return ConnectionInfo(
        host=parsed.hostname,
        port=parsed.port or args.port,
        user=unquote(parsed.username),
        password=unquote(parsed.password or ""),
        database=database_name,
        charset=charset,
        collation=collation,
        connect_timeout=int(connect_timeout_value),
    )


def connect(args: argparse.Namespace) -> Connection:
    connection_info = resolve_connection_info(args)
    ssl_ca_path = resolve_ssl_ca_path(args.ssl_ca_path)
    if ssl_ca_path is not None:
        return pymysql.connect(
            host=connection_info.host,
            port=connection_info.port,
            user=connection_info.user,
            password=connection_info.password,
            database=connection_info.database,
            charset=connection_info.charset,
            collation=connection_info.collation,
            connect_timeout=connection_info.connect_timeout,
            autocommit=False,
            ssl_ca=ssl_ca_path,
        )

    return pymysql.connect(
        host=connection_info.host,
        port=connection_info.port,
        user=connection_info.user,
        password=connection_info.password,
        database=connection_info.database,
        charset=connection_info.charset,
        collation=connection_info.collation,
        connect_timeout=connection_info.connect_timeout,
        autocommit=False,
    )


def upload_records(
    connection: Connection,
    records: list[ImageRecord],
    commit_every: int,
    connection_info: ConnectionInfo,
) -> None:
    if commit_every <= 0:
        raise ValueError("commit_every must be greater than 0")

    uploaded = 0
    with connection.cursor() as cursor:
        cursor.execute(
            f"SET NAMES {connection_info.charset} COLLATE {connection_info.collation}"
        )
        for index, record in enumerate(records, start=1):
            cursor.execute(
                INSERT_SQL,
                (
                    record.brand_key,
                    record.model_name,
                    record.source_filename,
                    record.mime_type,
                    record.payload,
                ),
            )
            uploaded += 1
            if index % commit_every == 0:
                connection.commit()
                print({"uploaded": uploaded, "last_model": record.model_name})

    connection.commit()
    print({"uploaded": uploaded, "status": "completed"})


def check_connection(connection: Connection, connection_info: ConnectionInfo) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            f"SET NAMES {connection_info.charset} COLLATE {connection_info.collation}"
        )
        cursor.execute("SELECT DATABASE()")
        row = cursor.fetchone()

    current_database = row[0] if row else None
    print(
        {
            "status": "connected",
            "host": connection_info.host,
            "port": connection_info.port,
            "database": current_database,
            "collation": connection_info.collation,
        }
    )


def main() -> None:
    args = parse_args()
    records = load_records(args.source_dir, args.brand)
    total_bytes = sum(len(record.payload) for record in records)
    connection_info = resolve_connection_info(args)

    if args.dry_run:
        print(
            {
                "dry_run": True,
                "image_count": len(records),
                "brand": args.brand,
                "total_bytes": total_bytes,
                "host": connection_info.host,
                "port": connection_info.port,
                "database": connection_info.database,
                "collation": connection_info.collation,
                "database_url_mode": bool(args.database_url),
            }
        )
        return

    if args.check_connection:
        connection = connect(args)
        try:
            check_connection(connection, connection_info)
        finally:
            connection.close()
        return

    connection = connect(args)
    try:
        upload_records(connection, records, args.commit_every, connection_info)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
