from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


class AugmentationManager:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.project_root.mkdir(parents=True, exist_ok=True)

    def build_config(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "horizontal_flip": bool(payload.get("horizontal_flip", True)),
            "vertical_flip": bool(payload.get("vertical_flip", False)),
            "rotation": int(payload.get("rotation", 15)),
            "brightness": float(payload.get("brightness", 0.1)),
            "contrast": float(payload.get("contrast", 0.1)),
            "noise": float(payload.get("noise", 0.02)),
            "scale": float(payload.get("scale", 0.1)),
        }

    def generate_augmented_variant(self, source_image: str, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source_image": source_image,
            "output_image": str(Path(source_image).with_name(Path(source_image).stem + "_augmented.png")),
            "config": config,
            "status": "ready",
        }
