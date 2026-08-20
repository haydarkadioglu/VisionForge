from __future__ import annotations

import base64
import re
import time
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from .annotation_manager import AnnotationManager
from .config import BASE_DIR, DATASET_DIR, EXPORT_DIR, FRONTEND_DIR, MODEL_DIR, RUN_DIR, load_app_config, save_app_config
from .dataset_manager import ensure_yaml_for_dataset, list_registered_datasets, scan_dataset
from .device_manager import detect_device
from .model_manager import download_model, get_model_by_id, list_models
from .trainer import training_service

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
annotation_manager = AnnotationManager(DATASET_DIR)


def _resolve_inference_model(model_id: str | None, model_path: str | None = None) -> str:
    if model_path:
        candidate = Path(model_path).expanduser()
        if not candidate.exists() and not candidate.is_absolute() and candidate.parent == Path('.'):
            for alternate_root in (MODEL_DIR, BASE_DIR):
                alternate = alternate_root / candidate.name
                if alternate.exists():
                    return str(alternate)
                if candidate.suffix == '':
                    fallback = alternate_root / f"{candidate.name}.pt"
                    if fallback.exists():
                        return str(fallback)
        if candidate.exists():
            return str(candidate)
        raise FileNotFoundError(f"Model file not found: {candidate}")

    if model_id:
        model = get_model_by_id(model_id)
        if model:
            candidate = Path(model["local_path"]).expanduser()
            return str(candidate)

    default_path = MODEL_DIR / "yolov8n.pt"
    return str(default_path)


def _decode_data_url(data_url: str, suffix: str) -> str:
    match = re.match(r"data:.*?;base64,(.*)", data_url)
    if not match:
        raise ValueError("Invalid base64 data URL")

    encoded = match.group(1)
    payload = base64.b64decode(encoded)
    target_dir = EXPORT_DIR / "live"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"inference_{int(time.time() * 1000)}.{suffix}"
    target_path.write_bytes(payload)
    return str(target_path)


def _normalize_inference_classes(model, classes):
    if not classes:
        return None

    names = getattr(model, "names", {}) or {}
    selected = set()
    for index, label in names.items():
        if str(label) in classes:
            selected.add(int(index))
    return sorted(selected) if selected else None


@app.route("/")
def index():
    return send_from_directory(str(FRONTEND_DIR), "index.html")


@app.route("/api/system", methods=["GET"])
def system_status():
    return jsonify({
        "device": detect_device(),
        "workspace": {
            "model_dir": str(MODEL_DIR),
            "dataset_dir": str(DATASET_DIR),
            "run_dir": str(RUN_DIR),
            "export_dir": str(EXPORT_DIR),
        },
    })


@app.route("/api/models", methods=["GET"])
def get_models():
    return jsonify({"items": list_models()})


@app.route("/api/models/download", methods=["POST"])
def download_selected_model():
    payload = request.get_json(silent=True) or {}
    model_id = payload.get("model_id")
    if not model_id:
        return jsonify({"error": "model_id is required"}), 400

    try:
        result = download_model(model_id)
        return jsonify({"result": result})
    except Exception as exc:  # pragma: no cover - runtime dependency specific
        return jsonify({"error": str(exc)}), 500


@app.route("/api/models/load", methods=["POST"])
def load_selected_model():
    payload = request.get_json(silent=True) or {}
    model_id = payload.get("model_id") or "yolov8n"
    model_path = payload.get("model_path")

    try:
        resolved_path = _resolve_inference_model(model_id, model_path)
        if not Path(resolved_path).exists():
            raise FileNotFoundError(f"Model file not found: {resolved_path}")
        return jsonify({"status": "loaded", "model_id": model_id, "model_path": resolved_path})
    except Exception as exc:  # pragma: no cover - optional dependency guard
        return jsonify({"error": str(exc)}), 400


@app.route("/api/datasets", methods=["GET"])
def list_datasets():
    payload = list_registered_datasets()
    return jsonify({"items": payload})


@app.route("/api/datasets/validate", methods=["POST"])
def validate_dataset():
    payload = request.get_json(silent=True) or {}
    dataset_path = payload.get("dataset_path") or str(DATASET_DIR)
    dataset_summary = scan_dataset(dataset_path)
    classes = payload.get("classes") or dataset_summary.get("class_names") or ["object"]
    yaml_path = ensure_yaml_for_dataset(dataset_path, classes)
    return jsonify({"dataset_path": dataset_path, "yaml_path": yaml_path, "status": "validated", "class_names": classes})


@app.route("/api/datasets/scan", methods=["POST"])
def scan_dataset_project():
    payload = request.get_json(silent=True) or {}
    folder_path = payload.get("folder_path") or str(DATASET_DIR)
    return jsonify(annotation_manager.scan_project(folder_path))


@app.route("/api/datasets/create", methods=["POST"])
def create_dataset_project():
    payload = request.get_json(silent=True) or {}
    project_name = payload.get("project_name") or "custom_dataset"
    source_dir = payload.get("source_dir") or str(DATASET_DIR)
    return jsonify(annotation_manager.create_project(project_name, source_dir))


@app.route("/api/datasets/inspect", methods=["POST"])
def inspect_dataset():
    payload = request.get_json(silent=True) or {}
    dataset_path = payload.get("dataset_path") or str(DATASET_DIR)
    return jsonify(scan_dataset(dataset_path))


@app.route("/api/datasets/augment", methods=["POST"])
def augment_dataset():
    payload = request.get_json(silent=True) or {}
    return jsonify({"status": "configured", "settings": payload})


@app.route("/api/annotations/load", methods=["POST"])
def load_annotations():
    payload = request.get_json(silent=True) or {}
    project_dir = payload.get("project_dir") or str(DATASET_DIR)
    return jsonify(annotation_manager.load_annotations(project_dir))


@app.route("/api/annotations/save", methods=["POST"])
def save_annotations():
    payload = request.get_json(silent=True) or {}
    project_dir = payload.get("project_dir") or str(DATASET_DIR)
    image_name = payload.get("image_name")
    annotations = payload.get("annotations") or []
    if not image_name:
        return jsonify({"error": "image_name is required"}), 400
    return jsonify(annotation_manager.save_annotations(project_dir, image_name, annotations))


@app.route("/api/training/start", methods=["POST"])
def start_training():
    payload = request.get_json(silent=True) or {}
    training_config = {
        "model_id": payload.get("model_id", "yolov8n"),
        "dataset_path": payload.get("dataset_path", str(DATASET_DIR)),
        "mode": payload.get("mode", "fine_tune"),
        "epochs": int(payload.get("epochs", 10)),
        "batch_size": int(payload.get("batch_size", 8)),
        "image_size": int(payload.get("image_size", 640)),
        "device": payload.get("device", detect_device()["device"]),
        "learning_rate": float(payload.get("learning_rate", 0.01)),
        "optimizer": payload.get("optimizer", "auto"),
    }
    return jsonify(training_service.start_training(training_config))


@app.route("/api/training/status", methods=["GET"])
def training_status():
    job_id = request.args.get("job_id")
    return jsonify(training_service.get_status(job_id))


@app.route("/api/inference", methods=["POST"])
def inference_preview():
    payload = request.get_json(silent=True) or {}
    classes = payload.get("classes") or []
    confidence = float(payload.get("confidence", 0.25))
    model_id = payload.get("model_id") or "yolov8n"
    model_path = payload.get("model_path")
    source_type = payload.get("source_type", "image")

    try:
        source = payload.get("image_path")
        if payload.get("image_data"):
            source = _decode_data_url(payload["image_data"], "jpg")
        elif payload.get("video_data"):
            source = _decode_data_url(payload["video_data"], "mp4")
        elif payload.get("video_path"):
            source = payload["video_path"]

        if not source:
            source = payload.get("image_path") or "demo/sample.jpg"

        resolved_model = _resolve_inference_model(model_id, model_path)
        if not Path(resolved_model).exists():
            raise FileNotFoundError(f"Model file not found: {resolved_model}")

        from ultralytics import YOLO

        model = YOLO(resolved_model)
        selected_classes = _normalize_inference_classes(model, classes)
        predict_kwargs = {
            "source": source,
            "conf": confidence,
            "iou": 0.45,
            "verbose": False,
            "project": str(RUN_DIR),
            "name": "inference-live",
            "exist_ok": True,
        }
        if selected_classes is not None:
            predict_kwargs["classes"] = selected_classes

        results = model.predict(**predict_kwargs)
        detections = []
        for result in results:
            boxes = getattr(result, "boxes", None)
            if boxes is None:
                continue
            for box in boxes:
                coords = box.xyxy[0].tolist()
                x1, y1, x2, y2 = [float(value) for value in coords]
                label_index = int(box.cls[0].item())
                label_name = result.names.get(label_index, str(label_index))
                detections.append({
                    "label": label_name,
                    "confidence": round(float(box.conf[0].item()), 3),
                    "bbox": [round(x1, 2), round(y1, 2), round(max(x2 - x1, 0.0), 2), round(max(y2 - y1, 0.0), 2)],
                })

        return jsonify({
            "status": "ready",
            "source_type": source_type,
            "classes": classes,
            "confidence": confidence,
            "model_path": resolved_model,
            "result": {
                "image_path": source,
                "detections": detections,
                "total_detections": len(detections),
            },
        })
    except Exception as exc:  # pragma: no cover - optional runtime dependency guard
        return jsonify({"error": str(exc), "status": "failed"}), 400


@app.route("/api/config", methods=["GET", "POST"])
def app_config():
    if request.method == "GET":
        return jsonify(load_app_config())

    payload = request.get_json(silent=True) or {}
    return jsonify(save_app_config(payload))


@app.route("/api/model/export", methods=["POST"])
def export_trained_model():
    payload = request.get_json(silent=True) or {}
    model_name = payload.get("model_name") or "best.pt"
    candidates = sorted(RUN_DIR.rglob(model_name))
    if not candidates:
        fallback = sorted(RUN_DIR.rglob("*.pt"))
        if not fallback:
            return jsonify({"error": "No trained model checkpoint was found in data/runs."}), 404
        candidates = fallback

    source_path = Path(candidates[-1])
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    export_path = EXPORT_DIR / f"{source_path.parent.name}-{source_path.name}"
    export_path.write_bytes(source_path.read_bytes())
    return jsonify({"status": "exported", "source": str(source_path), "export_path": str(export_path)})


@app.route("/api/export", methods=["GET"])
def export_listing():
    export_paths = []
    for directory in (EXPORT_DIR, RUN_DIR):
        if directory.exists():
            for child in sorted(directory.iterdir()):
                if child.is_file():
                    export_paths.append({"name": child.name, "size": child.stat().st_size, "path": str(child)})
    return jsonify({"items": export_paths})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "VisionForge backend"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
