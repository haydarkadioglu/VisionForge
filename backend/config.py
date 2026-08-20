import json
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = DATA_DIR / "models"
DATASET_DIR = DATA_DIR / "datasets"
RUN_DIR = DATA_DIR / "runs"
EXPORT_DIR = DATA_DIR / "exports"
APP_CONFIG_PATH = DATA_DIR / "visionforge_config.json"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
DATASET_DIR.mkdir(parents=True, exist_ok=True)
RUN_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def load_app_config() -> Dict[str, Any]:
    if not APP_CONFIG_PATH.exists():
        return {
            "dataset_path": str(DATASET_DIR),
            "last_model_id": "yolov8n",
            "last_model_path": str(MODEL_DIR / "yolov8n.pt"),
            "image_size": 640,
            "batch_size": 8,
            "epochs": 10,
            "confidence": 0.25,
            "normalization": "none",
            "last_page": "dashboard",
        }
    try:
        return json.loads(APP_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_app_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    merged = load_app_config()
    merged.update(payload)
    APP_CONFIG_PATH.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return merged
