from catboost import CatBoostRegressor
from pandas import CategoricalDtype
import pandas as pd


def build_regressor(model_params):
    return CatBoostRegressor(**dict(model_params))


def resolve_feature_columns(frame, target_column, feature_columns=None):
    if target_column not in frame.columns:
        raise ValueError(f"target column {target_column!r} was not found")

    if feature_columns is None:
        return [column for column in frame.columns if column != target_column]

    resolved_columns = list(feature_columns)
    missing_columns = [column for column in resolved_columns if column not in frame.columns]
    if missing_columns:
        raise ValueError(f"missing feature columns: {missing_columns}")
    if target_column in resolved_columns:
        raise ValueError("target column must not be included in feature_columns")
    return resolved_columns


def resolve_categorical_columns(frame, feature_columns, categorical_columns=None):
    if categorical_columns is not None:
        resolved_columns = list(categorical_columns)
        missing_columns = [column for column in resolved_columns if column not in feature_columns]
        if missing_columns:
            raise ValueError(f"categorical columns must be a subset of feature_columns: {missing_columns}")
        return resolved_columns

    resolved_columns = []
    for column in feature_columns:
        dtype = frame[column].dtype
        if isinstance(dtype, CategoricalDtype):
            resolved_columns.append(column)
            continue
        if pd.api.types.is_object_dtype(dtype) or pd.api.types.is_string_dtype(dtype):
            resolved_columns.append(column)
    return resolved_columns
