from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

from .config import DATASET_DIR


def _read_yaml(path: Path) -> Dict[str, Any]:
    if yaml is None:
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except Exception:
        return {}


def ensure_yaml_for_dataset(dataset_path: str, class_names: List[str] | None = None) -> str:
    base_path = Path(dataset_path)
    if not base_path.exists():
        base_path.mkdir(parents=True, exist_ok=True)

    data_yaml = base_path / "data.yaml"
    if not data_yaml.exists():
        names = class_names or ["object"]
        train_path = (base_path / "images" / "train").resolve()
        val_path = (base_path / "images" / "val").resolve()
        if not val_path.exists():
            val_path = train_path

        dataset_cfg = {
            "train": str(train_path),
            "val": str(val_path),
            "nc": len(names),
            "names": {idx: label for idx, label in enumerate(names)},
        }
        if yaml is not None:
            with data_yaml.open("w", encoding="utf-8") as handle:
                yaml.safe_dump(dataset_cfg, handle, sort_keys=False)
        else:
            data_yaml.write_text(
                "train: " + str(train_path) + "\n"
                "val: " + str(val_path) + "\n"
                "nc: " + str(len(names)) + "\n"
                "names: " + str({idx: label for idx, label in enumerate(names)}).replace("'", '"') + "\n",
                encoding="utf-8",
            )

    return str(data_yaml)


def scan_dataset(dataset_path: str) -> Dict[str, Any]:
    base_path = Path(dataset_path)
    images: List[str] = []
    labels: List[str] = []
    class_names: List[str] = []

    if base_path.exists():
        images = [
            str(path)
            for path in sorted(base_path.rglob("*.png"))
            + sorted(base_path.rglob("*.jpg"))
            + sorted(base_path.rglob("*.jpeg"))
        ]
        labels = [str(path) for path in sorted(base_path.rglob("*.txt"))]

    data_yaml = base_path / "data.yaml"
    yaml_data = _read_yaml(data_yaml)
    if yaml_data:
        names = yaml_data.get("names") or []
        if isinstance(names, dict):
            class_names = [names[str(idx)] for idx in sorted(names.keys(), key=lambda key: int(key))]
        else:
            class_names = [str(item) for item in names]

    if not class_names:
        class_names = sorted({path.stem for path in labels})

    if not data_yaml.exists() and base_path.exists():
        ensure_yaml_for_dataset(str(base_path), class_names or ["object"])

    return {
        "dataset_path": str(base_path),
        "exists": base_path.exists(),
        "image_count": len(images),
        "label_count": len(labels),
        "class_names": class_names,
        "samples": images[:5],
        "labels_preview": labels[:5],
        "status": "ready" if base_path.exists() else "not found",
        "datasets_root": str(DATASET_DIR),
        "yaml_path": str(data_yaml),
    }


def list_registered_datasets() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    if not DATASET_DIR.exists():
        return items

    for child in sorted(DATASET_DIR.iterdir()):
        if child.is_dir():
            items.append(scan_dataset(str(child)))
    return items
