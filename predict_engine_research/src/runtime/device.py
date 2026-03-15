try:
    import torch
except ImportError:
    torch = None


def get_device_report():
    if torch is None:
        return {
            "torch_installed": False,
            "preferred_device": "unavailable",
            "cuda_available": False,
            "mps_available": False,
        }

    mps_backend = getattr(torch.backends, "mps", None)
    cuda_available = torch.cuda.is_available()
    mps_available = bool(mps_backend is not None and mps_backend.is_available())

    if cuda_available:
        preferred_device = "cuda"
    elif mps_available:
        preferred_device = "mps"
    else:
        preferred_device = "cpu"

    return {
        "torch_installed": True,
        "torch_version": torch.__version__,
        "preferred_device": preferred_device,
        "cuda_available": cuda_available,
        "mps_available": mps_available,
    }
