from collections.abc import Mapping, Sequence
from functools import lru_cache

from external.predict_engine import (
    PredictEngineClient,
    PredictEnginePrediction,
    PredictEngineProjection,
    PredictEngineProjectionPoint,
    PredictScalar,
    get_predict_engine_client,
)


class PredictEngineService:

    def __init__(self, client: PredictEngineClient) -> None:
        self._client = client

    def connection_summary(self) -> dict[str, object]:
        return self._client.connection_summary()

    def health_summary(self) -> dict[str, object]:
        health = self._client.health()
        return {
            **self._client.connection_summary(),
            **health.as_dict(),
        }

    def predict(
        self,
        record: Mapping[str, PredictScalar] | None = None,
        *,
        request_id: str | None = None,
        **kwargs: PredictScalar,
    ) -> PredictEnginePrediction:
        return self._client.predict(record, request_id=request_id, **kwargs)


    def project(
        self,
        base_record: Mapping[str, PredictScalar] | None = None,
        *,
        feature_name: str,
        feature_values: Sequence[PredictScalar],
        request_id: str | None = None,
        **kwargs: PredictScalar,
    ) -> PredictEngineProjection:
        if not feature_name:
            raise ValueError("feature_name is required for predict-engine projection")
        if not feature_values:
            raise ValueError("feature_values must contain at least one item")

        seed_record = {} if base_record is None else dict(base_record)
        if kwargs:
            seed_record.update(kwargs)

        records: list[dict[str, PredictScalar]] = []
        labels: list[str] = []
        for feature_value in feature_values:
            projected_record = dict(seed_record)
            projected_record[feature_name] = feature_value
            records.append(projected_record)
            labels.append(str(feature_value))

        points: list[PredictEngineProjectionPoint] = []
        feature_columns: tuple[str, ...] = ()
        for label, projected_record, feature_value in zip(
            labels,
            records,
            feature_values,
            strict=True,
        ):
            prediction = self._client.predict(
                projected_record,
                request_id=request_id,
            )
            feature_columns = prediction.feature_columns
            points.append(
                PredictEngineProjectionPoint(
                    label=label,
                    feature_name=feature_name,
                    feature_value=feature_value,
                    predicted_price=prediction.predicted_price,
                )
            )

        return PredictEngineProjection(
            request_id=request_id or "",
            feature_name=feature_name,
            feature_columns=feature_columns,
            points=tuple(points),
        )


@lru_cache(maxsize=1)
def get_predict_engine_service() -> PredictEngineService:
    return PredictEngineService(client=get_predict_engine_client())
