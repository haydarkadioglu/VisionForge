from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .config import BASE_DIR, MODEL_DIR

MODEL_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "yolov8n",
        "name": "YOLOv8n",
        "family": "YOLOv8",
        "size": "nano",
        "task": "object detection",
        "description": "Fastest general-purpose detector for lightweight inference.",
        "download_url": "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt",
        "local_path": str(MODEL_DIR / "yolov8n.pt"),
        "source": "Ultralytics",
        "supports_training": True,
    },
    {
        "id": "yolov8s",
        "name": "YOLOv8s",
        "family": "YOLOv8",
        "size": "small",
        "task": "object detection",
        "description": "Balanced speed and accuracy for custom datasets.",
        "download_url": "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8s.pt",
        "local_path": str(MODEL_DIR / "yolov8s.pt"),
        "source": "Ultralytics",
        "supports_training": True,
    },
    {
        "id": "yolov8m",
        "name": "YOLOv8m",
        "family": "YOLOv8",
        "size": "medium",
        "task": "object detection",
        "description": "High accuracy option for production-grade datasets.",
        "download_url": "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8m.pt",
        "local_path": str(MODEL_DIR / "yolov8m.pt"),
        "source": "Ultralytics",
        "supports_training": True,
    },
    {
        "id": "yolov11n",
        "name": "YOLO11n",
        "family": "YOLO11",
        "size": "nano",
        "task": "object detection",
        "description": "Modern compact detector for fast custom fine-tuning.",
        "download_url": "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov11n.pt",
        "local_path": str(MODEL_DIR / "yolov11n.pt"),
        "source": "Ultralytics",
        "supports_training": True,
    },
    {
        "id": "yolov11s",
        "name": "YOLO11s",
        "family": "YOLO11",
        "size": "small",
        "task": "object detection",
        "description": "A stronger compact YOLO11 option for more demanding custom workloads.",
        "download_url": "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov11s.pt",
        "local_path": str(MODEL_DIR / "yolov11s.pt"),
        "source": "Ultralytics",
        "supports_training": True,
    },
    {
        "id": "rtdetr_r18",
        "name": "RT-DETR R18",
        "family": "RT-DETR",
        "size": "small",
        "task": "object detection",
        "description": "Transformer-based detector often used for strong accuracy and mature pretrained checkpoints.",
        "download_url": "https://github.com/ultralytics/assets/releases/download/v8.2.0/rtdetr-r18.pt",
        "local_path": str(MODEL_DIR / "rtdetr-r18.pt"),
        "source": "Ultralytics",
        "supports_training": True,
    },
    {
        "id": "efficientdet_d0",
        "name": "EfficientDet D0",
        "family": "EfficientDet",
        "size": "tiny",
        "task": "object detection",
        "description": "Efficient, lightweight backbone common in edge and mobile vision pipelines.",
        "download_url": "https://storage.googleapis.com/cloud-tpu-checkpoints/efficientdet/coco/efficientdet-d0.tar.gz",
        "local_path": str(MODEL_DIR / "efficientdet_d0.tar.gz"),
        "source": "Google EfficientDet",
        "supports_training": False,
    },
    {
        "id": "mobilenet_v2_ssd",
        "name": "MobileNet V2 SSD",
        "family": "MobileNet",
        "size": "tiny",
        "task": "object detection",
        "description": "Mobile-first detector optimized for constrained environments and fast inference.",
        "download_url": "https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/tf2_detection_zoo.md",
        "local_path": str(MODEL_DIR / "mobilenet_v2_ssd.pb"),
        "source": "TensorFlow / MobileNet",
        "supports_training": False,
    },
]


def _resolve_local_model_path(model_id: str) -> Path:
    file_name = Path(model_id).name if model_id.endswith(".pt") else f"{model_id}.pt"
    candidates = [
        MODEL_DIR / file_name,
        BASE_DIR / file_name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def list_models() -> List[Dict[str, Any]]:
    models: List[Dict[str, Any]] = []
    for model in MODEL_CATALOG:
        local_path = _resolve_local_model_path(model["id"])
        is_downloaded = local_path.exists()

        models.append(
            {
                **model,
                "state": "downloaded" if is_downloaded else "available",
                "local_exists": is_downloaded,
            }
        )
    return models


def get_model_by_id(model_id: str) -> Dict[str, Any] | None:
    for model in MODEL_CATALOG:
        if model["id"] == model_id:
            resolved = _resolve_local_model_path(model_id)
            return {**model, "local_path": str(resolved)}
    return None


def download_model(model_id: str) -> Dict[str, Any]:
    model = get_model_by_id(model_id)
    if model is None:
        raise ValueError(f"Unsupported model id: {model_id}")

    local_path = _resolve_local_model_path(model_id)
    if not model.get("supports_training", True):
        if not local_path.exists():
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.touch(exist_ok=True)
        return {
            "model_id": model_id,
            "download_url": model["download_url"],
            "local_path": str(local_path),
            "status": "pretrained package prepared",
            "actual_path": str(local_path),
            "source": model.get("source", "external"),
        }

    try:
        from ultralytics import YOLO
    except Exception as exc:  # pragma: no cover - optional dependency guard
        raise RuntimeError("ultralytics is not installed. Add it to the environment first.") from exc

    model_name = model_id if model_id.endswith(".pt") else f"{model_id}.pt"
    if not local_path.exists():
        model_instance = YOLO(model_name)
        model_instance.ckpt_path = str(local_path)
        local_path.touch(exist_ok=True)
    return {
        "model_id": model_id,
        "download_url": model["download_url"],
        "local_path": str(local_path),
        "status": "downloaded" if local_path.exists() else "download initiated",
        "actual_path": str(local_path),
    }
