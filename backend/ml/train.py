"""
Training script for pothole detection model.
Fine-tunes YOLOv8 on a pothole dataset.
"""
import os
import sys
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def train(
    data_yaml: str,
    model_variant: str = "yolov8n.pt",
    epochs: int = 50,
    batch: int = 16,
    imgsz: int = 640,
    output_dir: str = "ml/runs",
):
    """Fine-tune YOLOv8 on pothole dataset."""
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.error("ultralytics not installed. Run: pip install ultralytics")
        sys.exit(1)

    if not os.path.exists(data_yaml):
        logger.error(f"Dataset YAML not found: {data_yaml}")
        sys.exit(1)

    logger.info(f"Starting training: model={model_variant}, epochs={epochs}, batch={batch}")
    model = YOLO(model_variant)

    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        project=output_dir,
        name="pothole_v1",
        patience=10,
        save=True,
        pretrained=True,
        optimizer="AdamW",
        lr0=0.001,
        augment=True,
        mosaic=1.0,
        mixup=0.15,
        verbose=True,
    )

    best_model_path = str(results.save_dir / "weights" / "best.pt")
    logger.info(f"Training complete. Best model: {best_model_path}")
    return best_model_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLOv8 pothole detection model")
    parser.add_argument("--data", required=True, help="Path to data.yaml")
    parser.add_argument("--model", default="yolov8n.pt", help="Base model")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--output", default="ml/runs")
    args = parser.parse_args()

    best = train(args.data, args.model, args.epochs, args.batch, args.imgsz, args.output)
    print(f"\nBest model weights saved to: {best}")
