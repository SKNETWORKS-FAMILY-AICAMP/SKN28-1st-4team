# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportMissingImports=false, reportReturnType=false

from __future__ import annotations

import pandas as pd

from .schemas import VehicleCategoryMappingInput


REQUEST_COLUMNS = [
    "brand",
    "model_name",
    "class_name_examples",
    "level_name_examples",
    "context_summary",
]

MAPPING_TABLE_COLUMNS = [
    "brand",
    "model_name",
    "major_category",
    "market_family",
    "search_used",
    "note",
]


def build_mapping_requests(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(["brand", "model_name"], dropna=False)
        .agg(
            class_name_examples=("class_name", lambda series: _first_unique_values(series, limit=10)),
            level_name_examples=("level_name", lambda series: _first_unique_values(series, limit=10)),
            launch_price_min=("launch_price_krw", lambda series: _safe_number_summary(series, "min")),
            launch_price_max=("launch_price_krw", lambda series: _safe_number_summary(series, "max")),
            displacement_min=("displacement_cc", lambda series: _safe_number_summary(series, "min")),
            displacement_max=("displacement_cc", lambda series: _safe_number_summary(series, "max")),
            body_length_min=("body_length_mm", lambda series: _safe_number_summary(series, "min")),
            body_length_max=("body_length_mm", lambda series: _safe_number_summary(series, "max")),
        )
        .reset_index()
    )
    grouped["context_summary"] = grouped.apply(_build_context_summary, axis=1)
    return grouped[REQUEST_COLUMNS]


def dataframe_to_mapping_inputs(df: pd.DataFrame) -> list[VehicleCategoryMappingInput]:
    inputs: list[VehicleCategoryMappingInput] = []
    for row in df.to_dict(orient="records"):
        inputs.append(
            VehicleCategoryMappingInput(
                brand=row["brand"],
                model_name=row["model_name"],
                class_name_examples=row.get("class_name_examples") or [],
                level_name_examples=row.get("level_name_examples") or [],
                context_summary=row.get("context_summary"),
            )
        )
    return inputs


def load_mapping_table(path) -> pd.DataFrame:
    path = _as_path(path)
    if not path.exists():
        return pd.DataFrame(columns=MAPPING_TABLE_COLUMNS)
    frame = pd.read_csv(path, dtype=str)
    for column in MAPPING_TABLE_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.NA
    return frame[MAPPING_TABLE_COLUMNS]


def get_pending_requests(requests_df: pd.DataFrame, mapping_df: pd.DataFrame) -> pd.DataFrame:
    done_keys = set(zip(mapping_df["brand"], mapping_df["model_name"]))
    pending_mask = ~requests_df.apply(lambda row: (row["brand"], row["model_name"]) in done_keys, axis=1)
    return requests_df.loc[pending_mask].copy()


def derive_market_family(major_category: str) -> str:
    if major_category in {"sedan", "hatchback", "wagon", "coupe_convertible"}:
        return "sedan"
    if major_category == "suv":
        return "suv"
    if major_category == "unknown":
        return "unknown"
    return "other"


def apply_mapping_table(input_df: pd.DataFrame, mapping_df: pd.DataFrame) -> pd.DataFrame:
    mapping_core = mapping_df[["brand", "model_name", "major_category", "market_family"]].drop_duplicates()
    return input_df.merge(mapping_core, on=["brand", "model_name"], how="left")


def _first_unique_values(series: pd.Series, limit: int) -> list[str]:
    values: list[str] = []
    for value in series.dropna().tolist():
        normalized = str(value).strip()
        if normalized and normalized not in values:
            values.append(normalized)
        if len(values) >= limit:
            break
    return values


def _safe_number_summary(series: pd.Series, op: str) -> int | None:
    numeric_series = pd.Series(pd.to_numeric(series, errors="coerce"), dtype="float64")
    numeric_values = [float(value) for value in numeric_series.tolist() if pd.notna(value)]
    if not numeric_values:
        return None
    if op == "min":
        return int(min(numeric_values))
    if op == "max":
        return int(max(numeric_values))
    raise ValueError(f"Unsupported op: {op}")


def _build_context_summary(row: pd.Series) -> str:
    parts: list[str] = []
    if row.get("class_name_examples"):
        parts.append(f"class_name_examples={', '.join(row['class_name_examples'])}")
    if row.get("level_name_examples"):
        parts.append(f"level_name_examples={', '.join(row['level_name_examples'])}")
    if row.get("launch_price_min") is not None or row.get("launch_price_max") is not None:
        parts.append(f"launch_price_range_krw={row.get('launch_price_min')}~{row.get('launch_price_max')}")
    if row.get("displacement_min") is not None or row.get("displacement_max") is not None:
        parts.append(f"displacement_range_cc={row.get('displacement_min')}~{row.get('displacement_max')}")
    if row.get("body_length_min") is not None or row.get("body_length_max") is not None:
        parts.append(f"body_length_range_mm={row.get('body_length_min')}~{row.get('body_length_max')}")
    return " | ".join(parts)


def _as_path(path_like):
    from pathlib import Path

    return path_like if hasattr(path_like, "exists") else Path(path_like)
