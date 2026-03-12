import importlib
from pathlib import Path
from typing import Any

onnx = importlib.import_module("onnx")
torch = importlib.import_module("torch")


def detect_device() -> Any:
    if torch.cuda.is_available():
        return torch.device("cuda")

    mps_backend = getattr(torch.backends, "mps", None)
    if (
        mps_backend is not None
        and mps_backend.is_built()
        and mps_backend.is_available()
    ):
        return torch.device("mps")

    return torch.device("cpu")


def move_batch_to_device(
    features: Any,
    targets: Any,
    device: Any,
) -> tuple[Any, Any]:
    use_non_blocking = device.type == "cuda"

    if use_non_blocking:
        features = features.pin_memory()
        targets = targets.pin_memory()

    return (
        features.to(device, non_blocking=use_non_blocking),
        targets.to(device, non_blocking=use_non_blocking),
    )


def run_training_step(device: Any) -> dict[str, object]:
    model = torch.nn.Linear(8, 2).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = torch.nn.MSELoss()

    features = torch.randn(32, 8)
    targets = torch.randn(32, 2)
    features, targets = move_batch_to_device(features, targets, device)

    model.train()
    optimizer.zero_grad()
    predictions = model(features)
    loss = criterion(predictions, targets)
    loss.backward()
    optimizer.step()

    return {
        "input_device": str(features.device),
        "target_device": str(targets.device),
        "model_device": str(model.weight.device),
        "loss": round(loss.item(), 6),
    }


def main() -> None:
    device = detect_device()
    output_dir = Path(__file__).resolve().parents[1] / "models"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(
        {
            "service": "predict_engine_research",
            "device": str(device),
            "training_step": run_training_step(device),
            "model_output_dir": str(output_dir),
            "torch_version": torch.__version__,
            "onnx_version": onnx.__version__,
        }
    )


if __name__ == "__main__":
    main()
