from __future__ import annotations

import csv
import math
from bisect import bisect_left, bisect_right
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from statistics import mean, median

from ..bmt_add_cat import (
    CategoryStore,
    load_category_store,
    normalize_text,
)

from .config import DEFAULT_INPUT_TABLE_PATH


GEOMETRY_FIELDS = ("body_length_mm", "body_width_mm", "body_height_mm")
DEFAULT_CLASS_PLACEHOLDER = "__base_class__"


@dataclass(frozen=True)
class TupleSample:
    brand: str
    model_name: str
    class_name: str
    major_category: str
    displacement_cc: float
    body_length_mm: float
    body_width_mm: float
    body_height_mm: float

    @property
    def lookup_key(self) -> tuple[str, str, str]:
        return (
            normalize_text(self.brand),
            normalize_text(self.model_name),
            _normalize_class_name(self.class_name),
        )


@dataclass(frozen=True)
class TupleRecord:
    brand: str
    model_name: str
    class_name: str
    major_category: str
    displacement_cc: float
    body_length_mm: float
    body_width_mm: float
    body_height_mm: float

    @property
    def lookup_key(self) -> tuple[str, str, str]:
        return (
            normalize_text(self.brand),
            normalize_text(self.model_name),
            _normalize_class_name(self.class_name),
        )


class ScoreStore:
    def __init__(
        self,
        input_table_path: Path | str = DEFAULT_INPUT_TABLE_PATH,
        *,
        category_store: CategoryStore | None = None,
    ) -> None:
        self.source_path = Path(input_table_path).resolve()
        self.category_store = category_store or load_category_store()
        self._score_lookup: dict[tuple[str, str, str], float] = {}
        self._load()

    @classmethod
    def from_path(
        cls,
        path: Path | str = DEFAULT_INPUT_TABLE_PATH,
        *,
        category_store: CategoryStore | None = None,
    ) -> "ScoreStore":
        return cls(input_table_path=path, category_store=category_store)

    def get_size_score(
        self,
        brand: str | None,
        model_name: str | None,
        class_name: str | None,
    ) -> float | None:
        normalized_brand = normalize_text(brand)
        normalized_model = normalize_text(model_name)
        if not normalized_brand or not normalized_model:
            return None

        exact_class = _normalize_class_name(class_name)
        if exact_class:
            exact_key = (normalized_brand, normalized_model, exact_class)
            exact_score = self._score_lookup.get(exact_key)
            if exact_score is not None:
                return exact_score

        fallback_key = (normalized_brand, normalized_model, DEFAULT_CLASS_PLACEHOLDER)
        return self._score_lookup.get(fallback_key)

    def _load(self) -> None:
        if not self.source_path.exists():
            raise FileNotFoundError(f"Score input table not found: {self.source_path}")

        grouped_samples: dict[tuple[str, str, str], list[TupleSample]] = defaultdict(list)

        with self.source_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            required_columns = {
                "brand",
                "model_name",
                "class_name",
                "displacement_cc",
                "body_length_mm",
                "body_width_mm",
                "body_height_mm",
            }
            fieldnames = set(reader.fieldnames or [])
            missing = required_columns - fieldnames
            if missing:
                missing_text = ", ".join(sorted(missing))
                raise ValueError(f"Missing required columns in {self.source_path}: {missing_text}")

            for row in reader:
                sample = self._build_sample(row)
                if sample is None:
                    continue
                grouped_samples[sample.lookup_key].append(sample)

        records = [self._aggregate_samples(samples) for samples in grouped_samples.values()]
        records_by_category: dict[str, list[TupleRecord]] = defaultdict(list)
        for record in records:
            records_by_category[record.major_category].append(record)

        for category_records in records_by_category.values():
            self._register_category_scores(category_records)

    def _build_sample(self, row: dict[str, str]) -> TupleSample | None:
        brand = (row.get("brand") or "").strip()
        model_name = (row.get("model_name") or "").strip()
        class_name = (row.get("class_name") or "").strip()
        if not brand or not model_name or not class_name:
            return None

        canonical_brand, canonical_model, major_category = self.category_store.resolve(brand, model_name)
        if major_category is None or canonical_brand is None or canonical_model is None:
            return None

        geometry_values = [self._parse_positive_float(row, field) for field in GEOMETRY_FIELDS]
        if any(value is None for value in geometry_values):
            return None

        displacement_cc = self._parse_non_negative_float(row, "displacement_cc")
        if displacement_cc is None:
            return None

        return TupleSample(
            brand=canonical_brand,
            model_name=canonical_model,
            class_name=class_name,
            major_category=major_category,
            displacement_cc=displacement_cc,
            body_length_mm=geometry_values[0],
            body_width_mm=geometry_values[1],
            body_height_mm=geometry_values[2],
        )

    def _aggregate_samples(self, samples: list[TupleSample]) -> TupleRecord:
        first = samples[0]
        return TupleRecord(
            brand=first.brand,
            model_name=first.model_name,
            class_name=first.class_name,
            major_category=first.major_category,
            displacement_cc=median(sample.displacement_cc for sample in samples),
            body_length_mm=median(sample.body_length_mm for sample in samples),
            body_width_mm=median(sample.body_width_mm for sample in samples),
            body_height_mm=median(sample.body_height_mm for sample in samples),
        )

    def _register_category_scores(self, records: list[TupleRecord]) -> None:
        length_logs = [math.log(record.body_length_mm) for record in records]
        width_logs = [math.log(record.body_width_mm) for record in records]
        height_logs = [math.log(record.body_height_mm) for record in records]
        displacement_logs = [math.log1p(record.displacement_cc) for record in records]

        length_mean, length_std = _population_stats(length_logs)
        width_mean, width_std = _population_stats(width_logs)
        height_mean, height_std = _population_stats(height_logs)
        displacement_mean, displacement_std = _population_stats(displacement_logs)

        raw_scores: dict[tuple[str, str, str], float] = {}
        for record in records:
            body_score = mean(
                [
                    _zscore(math.log(record.body_length_mm), length_mean, length_std),
                    _zscore(math.log(record.body_width_mm), width_mean, width_std),
                    _zscore(math.log(record.body_height_mm), height_mean, height_std),
                ]
            )
            displacement_score = _zscore(
                math.log1p(record.displacement_cc),
                displacement_mean,
                displacement_std,
            )
            raw_scores[record.lookup_key] = (0.8 * body_score) + (0.2 * displacement_score)

        sorted_raw_scores = sorted(raw_scores.values())
        for lookup_key, raw_score in raw_scores.items():
            self._score_lookup[lookup_key] = _percentile_rank(raw_score, sorted_raw_scores)

    @staticmethod
    def _parse_positive_float(row: dict[str, str], key: str) -> float | None:
        raw = (row.get(key) or "").strip()
        if not raw:
            return None
        value = float(raw)
        if value <= 0:
            return None
        return value

    @staticmethod
    def _parse_non_negative_float(row: dict[str, str], key: str) -> float | None:
        raw = (row.get(key) or "").strip()
        if not raw:
            return None
        value = float(raw)
        if value < 0:
            return None
        return value


def _population_stats(values: list[float]) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    value_mean = mean(values)
    variance = sum((value - value_mean) ** 2 for value in values) / len(values)
    return (value_mean, math.sqrt(variance))


def _zscore(value: float, value_mean: float, value_std: float) -> float:
    if value_std == 0:
        return 0.0
    return (value - value_mean) / value_std


def _percentile_rank(value: float, sorted_values: list[float]) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return 50.0
    left = bisect_left(sorted_values, value)
    right = bisect_right(sorted_values, value)
    average_position = (left + right - 1) / 2
    return 100.0 * average_position / (len(sorted_values) - 1)


def _normalize_class_name(class_name: str | None) -> str:
    raw = (class_name or "").strip()
    normalized = normalize_text(raw)
    if normalized:
        return normalized
    if raw == "-":
        return DEFAULT_CLASS_PLACEHOLDER
    return ""


@lru_cache(maxsize=2)
def load_score_store(path: Path | str = DEFAULT_INPUT_TABLE_PATH) -> ScoreStore:
    return ScoreStore.from_path(path)


def get_size_score(
    brand: str | None,
    model_name: str | None,
    class_name: str | None,
    *,
    store: ScoreStore | None = None,
) -> float | None:
    active_store = store or load_score_store()
    return active_store.get_size_score(brand, model_name, class_name)
