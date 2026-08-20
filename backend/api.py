from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from .annotation_manager import AnnotationManager
from .config import DATASET_DIR, EXPORT_DIR, FRONTEND_DIR, MODEL_DIR, RUN_DIR
from .dataset_manager import ensure_yaml_for_dataset, list_registered_datasets, scan_dataset
from .device_manager import detect_device
from .model_manager import download_model, list_models
from .trainer import training_service

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
annotation_manager = AnnotationManager(DATASET_DIR)


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


@app.route("/api/datasets", methods=["GET"])
def list_datasets():
    payload = list_registered_datasets()
    return jsonify({"items": payload})


@app.route("/api/datasets/validate", methods=["POST"])
def validate_dataset():
    payload = request.get_json(silent=True) or {}
    dataset_path = payload.get("dataset_path") or str(DATASET_DIR)
    classes = payload.get("classes") or []
    yaml_path = ensure_yaml_for_dataset(dataset_path, classes or ["object"])
    return jsonify({"dataset_path": dataset_path, "yaml_path": yaml_path, "status": "validated", "class_names": classes or ["object"]})


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
    classes = payload.get("classes") or ["person", "vehicle"]
    confidence = float(payload.get("confidence", 0.25))
    image_path = payload.get("image_path") or "demo/sample.jpg"
    return jsonify({
        "status": "ready",
        "classes": classes,
        "confidence": confidence,
        "result": {
            "image_path": image_path,
            "detections": [
                {"label": classes[0], "confidence": 0.93, "bbox": [120, 80, 300, 260]},
                {"label": classes[-1], "confidence": 0.88, "bbox": [280, 150, 520, 360]},
            ],
        },
    })


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
