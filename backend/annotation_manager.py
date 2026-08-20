from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class AnnotationManager:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.project_root.mkdir(parents=True, exist_ok=True)

    def scan_project(self, folder_path: str) -> Dict[str, Any]:
        base_path = Path(folder_path)
        images = []
        if base_path.exists():
            images = sorted(
                [
                    str(path)
                    for path in base_path.iterdir()
                    if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
                ]
            )

        return {
            "folder_path": str(base_path),
            "exists": base_path.exists(),
            "image_count": len(images),
            "images": images[:25],
            "status": "ready" if base_path.exists() else "not found",
        }

    def create_project(self, project_name: str, source_dir: str) -> Dict[str, Any]:
        source_path = Path(source_dir)
        project_dir = self.project_root / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        images_dir = project_dir / "images"
        labels_dir = project_dir / "labels"
        images_dir.mkdir(exist_ok=True)
        labels_dir.mkdir(exist_ok=True)

        manifest = {
            "project_name": project_name,
            "source_dir": str(source_path),
            "created_at": str(Path.cwd()),
            "images": [],
            "classes": ["object"],
        }
        (project_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return {
            "project_name": project_name,
            "project_dir": str(project_dir),
            "status": "created",
            "image_count": self.scan_project(str(source_path))["image_count"],
        }

    def load_annotations(self, project_dir: str) -> Dict[str, Any]:
        manifest_path = Path(project_dir) / "manifest.json"
        if not manifest_path.exists():
            return {"annotations": [], "classes": ["object"], "status": "empty"}

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return {
            "annotations": manifest.get("images", []),
            "classes": manifest.get("classes", ["object"]),
            "status": "loaded",
        }

    def save_annotations(self, project_dir: str, image_name: str, annotations: List[Dict[str, Any]]) -> Dict[str, Any]:
        manifest_path = Path(project_dir) / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"images": [], "classes": ["object"]}
        existing = {item.get("image_name"): item for item in manifest.get("images", [])}
        existing[image_name] = {"image_name": image_name, "annotations": annotations}
        manifest["images"] = list(existing.values())
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return {"status": "saved", "image_name": image_name, "annotations": annotations}
