from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = DATA_DIR / "models"
DATASET_DIR = DATA_DIR / "datasets"
RUN_DIR = DATA_DIR / "runs"
EXPORT_DIR = DATA_DIR / "exports"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
DATASET_DIR.mkdir(parents=True, exist_ok=True)
RUN_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
