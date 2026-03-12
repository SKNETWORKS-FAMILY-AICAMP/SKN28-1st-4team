from dataclasses import dataclass


PredictScalar = float | int | str | bool | None


@dataclass(frozen=True)
class PredictEngineHealth:
    status: str
    service_name: str
    model_path: str
    model_exists: bool
    model_loaded: bool
    model_input_name: str
    model_output_names: tuple[str, ...]
    model_error: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "service_name": self.service_name,
            "model_path": self.model_path,
            "model_exists": self.model_exists,
            "model_loaded": self.model_loaded,
            "model_input_name": self.model_input_name,
            "model_output_names": list(self.model_output_names),
            "model_error": self.model_error,
        }


@dataclass(frozen=True)
class PredictEngineTensor:
    name: str
    dtype: str
    shape: tuple[int, ...]
    values: tuple[float | int | str | bool, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "dtype": self.dtype,
            "shape": list(self.shape),
            "values": list(self.values),
        }


@dataclass(frozen=True)
class PredictEnginePrediction:
    request_id: str
    outputs: tuple[PredictEngineTensor, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "outputs": [output.as_dict() for output in self.outputs],
        }
