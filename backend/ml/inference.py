"""
YOLOv8 inference script for standalone pothole detection.
"""
import argparse
import os
import json
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_inference(image_path: str, model_path: str, output_dir: str, conf: float = 0.5):
    """Run YOLOv8 inference on a single image or directory."""
    try:
        from ultralytics import YOLO
        import cv2
    except ImportError:
        logger.error("ultralytics and opencv-python are required. Install via: pip install ultralytics opencv-python")
        sys.exit(1)

    model = YOLO(model_path)
    os.makedirs(output_dir, exist_ok=True)

    paths = [image_path]
    if os.path.isdir(image_path):
        exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
        paths = [str(p) for p in Path(image_path).iterdir() if p.suffix.lower() in exts]

    all_results = []
    for path in paths:
        logger.info(f"Processing: {path}")
        results = model(path, conf=conf, verbose=False)
        detections = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                det = {
                    "bbox": [x1, y1, x2, y2],
                    "confidence": float(box.conf[0]),
                    "class": int(box.cls[0]),
                    "class_name": model.names[int(box.cls[0])],
                }
                detections.append(det)

        # Annotate and save
        annotated = results[0].plot() if results else None
        if annotated is not None:
            out_path = os.path.join(output_dir, f"annotated_{Path(path).name}")
            cv2.imwrite(out_path, annotated)
            logger.info(f"Saved annotated image: {out_path}")

        all_results.append({"image": path, "detections": detections})

    # Save results JSON
    json_path = os.path.join(output_dir, "results.json")
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2)
    logger.info(f"Results saved to {json_path}")

    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YOLOv8 Pothole Detection Inference")
    parser.add_argument("--image", required=True, help="Path to image or directory")
    parser.add_argument("--model", default="yolov8n.pt", help="Path to YOLO model")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--conf", type=float, default=0.5, help="Confidence threshold")
    args = parser.parse_args()

    results = run_inference(args.image, args.model, args.output, args.conf)
    total = sum(len(r["detections"]) for r in results)
    print(f"\nDetected {total} potholes across {len(results)} image(s).")
