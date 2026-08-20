from __future__ import annotations

from typing import Any, Dict

try:
    import torch
except Exception:  # pragma: no cover - optional dependency guard
    torch = None


def detect_device() -> Dict[str, Any]:
    if torch is None:
        return {
            "cuda_available": False,
            "device": "cpu",
            "device_count": 0,
            "device_name": "CPU",
            "torch_version": "unknown",
            "status": "CPU fallback active",
        }

    cuda_available = torch.cuda.is_available()
    if cuda_available:
        device_name = torch.cuda.get_device_name(0)
        device = "cuda"
        status = "CUDA detected, GPU training enabled"
        device_count = torch.cuda.device_count()
    else:
        device_name = "CPU"
        device = "cpu"
        status = "CUDA not detected, using CPU"
        device_count = 0

    return {
        "cuda_available": cuda_available,
        "device": device,
        "device_count": device_count,
        "device_name": device_name,
        "torch_version": torch.__version__,
        "status": status,
    }
