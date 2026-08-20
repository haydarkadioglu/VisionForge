# VisionForge

VisionForge is a desktop-style computer vision workspace for custom YOLO workflows. It combines a dashboard UI, dataset preparation, model management, annotation support, training orchestration, and live inference in one local application.

## Features

- Model catalog with popular pretrained detectors
- Custom dataset preparation and label management
- Annotation workspace for drawing bounding boxes
- Training configuration for fine-tune and from-scratch runs
- GPU detection with CPU fallback
- Live webcam, photo, and video inference
- Local model loading for custom weights such as best.pt

## Supported models

- YOLOv8n / YOLOv8s / YOLOv8m
- YOLO11n / YOLO11s
- RT-DETR R18
- EfficientDet D0
- MobileNet V2 SSD

These can be used as base models or loaded as custom exported checkpoints for inference.

## Requirements

- Python 3.10+
- PyTorch
- Ultralytics
- Flask
- pywebview

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the app

From the project root:

```bash
python app.py
```

This launches the VisionForge desktop shell and starts the local backend service.

## How to use

1. Open the app and go to Models.
2. Download or select a model from the catalog.
3. Prepare a dataset or scan an existing dataset folder.
4. Use the annotation workspace to label images.
5. Start training from the Training page.
6. Run inference from the Inference page using webcam, image, or video input.
7. Load a custom .pt file in the inference panel to test your own trained weights.

## Notes

- Local checkpoints are expected under the project workspace or the data/models directory.
- CPU mode works automatically if GPU is unavailable.
- For best results, use a dataset with train and validation splits and consistent class names.
