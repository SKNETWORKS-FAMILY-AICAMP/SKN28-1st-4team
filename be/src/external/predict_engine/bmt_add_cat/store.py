from __future__ import annotations

import csv
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from .config import DEFAULT_MAPPING_TABLE_PATH


class CategoryStore:
    def __init__(self, mapping_table_path: Path | str = DEFAULT_MAPPING_TABLE_PATH) -> None:
        self.source_path = Path(mapping_table_path).resolve()
        self._category_lookup: dict[tuple[str, str], str] = {}
        self._brand_lookup: dict[str, str] = {}
        self._model_lookup: dict[tuple[str, str], str] = {}
        self._load()

    @classmethod
    def from_path(cls, path: Path | str = DEFAULT_MAPPING_TABLE_PATH) -> "CategoryStore":
        return cls(mapping_table_path=path)

    def get_major_category(self, brand: str | None, model_name: str | None) -> str | None:
        normalized_brand = normalize_text(brand)
        normalized_model = normalize_text(model_name)
        if not normalized_brand or not normalized_model:
            return None
        return self._category_lookup.get((normalized_brand, normalized_model))

    def get_major_category_from_tuple(
        self,
        brand: str | None,
        model_name: str | None,
        trim_name: str | None = None,
    ) -> str | None:
        del trim_name
        return self.get_major_category(brand, model_name)

    def resolve(
        self,
        brand: str | None,
        model_name: str | None,
        trim_name: str | None = None,
    ) -> tuple[str | None, str | None, str | None]:
        del trim_name
        normalized_brand = normalize_text(brand)
        normalized_model = normalize_text(model_name)
        if not normalized_brand or not normalized_model:
            return (None, None, None)

        key = (normalized_brand, normalized_model)
        category = self._category_lookup.get(key)
        if category is None:
            return (None, None, None)

        canonical_brand = self._brand_lookup.get(normalized_brand, brand)
        canonical_model = self._model_lookup.get(key, model_name)
        return (canonical_brand, canonical_model, category)

    def _load(self) -> None:
        if not self.source_path.exists():
            raise FileNotFoundError(f"Category mapping table not found: {self.source_path}")

        with self.source_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            required_columns = {"brand", "model_name", "major_category"}
            fieldnames = set(reader.fieldnames or [])
            missing = required_columns - fieldnames
            if missing:
                missing_text = ", ".join(sorted(missing))
                raise ValueError(f"Missing required columns in {self.source_path}: {missing_text}")

            for row in reader:
                brand = (row.get("brand") or "").strip()
                model_name = (row.get("model_name") or "").strip()
                major_category = (row.get("major_category") or "").strip()
                if not brand or not model_name or not major_category:
                    continue

                normalized_brand = normalize_text(brand)
                normalized_model = normalize_text(model_name)
                key = (normalized_brand, normalized_model)

                existing_category = self._category_lookup.get(key)
                if existing_category and existing_category != major_category:
                    raise ValueError(
                        "Conflicting major_category values for "
                        f"{brand} / {model_name}: {existing_category} vs {major_category}"
                    )

                self._category_lookup[key] = major_category
                self._brand_lookup.setdefault(normalized_brand, brand)
                self._model_lookup.setdefault(key, model_name)


def normalize_text(text: str | None) -> str:
    if text is None:
        return ""
    normalized = unicodedata.normalize("NFKC", str(text)).casefold()
    normalized = re.sub(r"[^0-9a-zA-Z가-힣]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


@lru_cache(maxsize=4)
def load_category_store(path: Path | str = DEFAULT_MAPPING_TABLE_PATH) -> CategoryStore:
    return CategoryStore.from_path(path)


def get_major_category(
    brand: str | None,
    model_name: str | None,
    *,
    store: CategoryStore | None = None,
) -> str | None:
    active_store = store or load_category_store()
    return active_store.get_major_category(brand, model_name)


def get_major_category_from_tuple(
    brand: str | None,
    model_name: str | None,
    trim_name: str | None = None,
    *,
    store: CategoryStore | None = None,
) -> str | None:
    active_store = store or load_category_store()
    return active_store.get_major_category_from_tuple(brand, model_name, trim_name)
