from dataclasses import dataclass

from ..types import PredictScalar


@dataclass(frozen=True)
class PredictEngineFeatureVector:
    """Feature ordering is not finalized yet; keep it aligned with the training manifest."""

    ordered_items: tuple[tuple[str, PredictScalar], ...]

    @property
    def feature_names(self) -> tuple[str, ...]:
        return tuple(name for name, _ in self.ordered_items)

    @property
    def values(self) -> tuple[PredictScalar, ...]:
        return tuple(value for _, value in self.ordered_items)

    def as_dict(self) -> dict[str, PredictScalar]:
        return dict(self.ordered_items)
