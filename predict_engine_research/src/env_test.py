import json

import importlib
from typing import Any

from main import detect_device

torch = importlib.import_module("torch")


def test_device(device: Any) -> dict[str, object]:
    try:
        x = torch.randn(4, 4, device=device)
        y = torch.randn(4, 4, device=device)
        z = x @ y
        return {
            "ok": True,
            "device": str(device),
            "result_device": str(z.device),
            "result_shape": list(z.shape),
            "result_sum": round(z.sum().item(), 6),
        }
    except Exception as exc:
        return {
            "ok": False,
            "device": str(device),
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> None:
    mps_backend = getattr(torch.backends, "mps", None)
    selected_device = detect_device()

    report = {
        "selected_device": str(selected_device),
        "cuda_available": torch.cuda.is_available(),
        "mps_built": mps_backend is not None and mps_backend.is_built(),
        "mps_available": mps_backend is not None and mps_backend.is_available(),
        "device_test": test_device(selected_device),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
