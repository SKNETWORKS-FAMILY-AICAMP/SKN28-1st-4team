from ...types import PredictScalar


def normalize_car_record(
    record: dict[str, PredictScalar],
) -> dict[str, PredictScalar]:
    normalized: dict[str, PredictScalar] = {}
    for key, value in record.items():
        if isinstance(value, str):
            normalized[key] = value.strip()
        else:
            normalized[key] = value
    return normalized
