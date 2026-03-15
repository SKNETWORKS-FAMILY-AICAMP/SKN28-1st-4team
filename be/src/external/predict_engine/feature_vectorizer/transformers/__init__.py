from .base import FeatureTransformer
from .car_record import normalize_car_record


def build_default_transformers():
    return [normalize_car_record]


__all__ = [
    "FeatureTransformer",
    "build_default_transformers",
    "normalize_car_record",
]
