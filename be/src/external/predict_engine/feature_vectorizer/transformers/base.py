from typing import Protocol

from ...types import PredictScalar


class FeatureTransformer(Protocol):
    def __call__(
        self,
        record: dict[str, PredictScalar],
    ) -> dict[str, PredictScalar]: ...
