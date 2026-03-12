"""
Download pretrained YOLOv8 model for pothole detection.
"""
import os
import sys
import logging
import argparse
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_VARIANTS = {
    "nano": "yolov8n.pt",
    "small": "yolov8s.pt",
    "medium": "yolov8m.pt",
}

POTHOLE_MODEL_URL = (
    "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt"
)


def download_model(variant: str = "nano", output_dir: str = "ml/models"):
    """Download a YOLOv8 model using ultralytics."""
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.error("ultralytics not installed. Run: pip install ultralytics")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    filename = MODEL_VARIANTS.get(variant, "yolov8n.pt")
    output_path = os.path.join(output_dir, filename)

    if os.path.exists(output_path):
        logger.info(f"Model already exists at {output_path}. Skipping download.")
        return output_path

    logger.info(f"Downloading YOLOv8 {variant} model...")
    model = YOLO(filename)  # ultralytics auto-downloads
    # Copy to our models directory
    import shutil
    downloaded = Path(filename)
    if downloaded.exists():
        shutil.move(str(downloaded), output_path)
        logger.info(f"Model saved to {output_path}")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download YOLOv8 model")
    parser.add_argument(
        "--variant",
        default="nano",
        choices=list(MODEL_VARIANTS.keys()),
        help="Model size variant",
    )
    parser.add_argument("--output", default="ml/models", help="Output directory")
    args = parser.parse_args()
    path = download_model(args.variant, args.output)
    print(f"Model ready at: {path}")
