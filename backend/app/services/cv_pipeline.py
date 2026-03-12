"""
Computer Vision Pipeline for Pothole Detection.
Uses YOLOv8 for real-time and batch detection.
"""
import os
import io
import uuid
import logging
from pathlib import Path
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)

try:
    import cv2
    from ultralytics import YOLO
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False
    logger.warning("OpenCV/YOLO not available; using mock detection mode.")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class DetectionResult:
    """Represents a single pothole detection."""

    def __init__(
        self,
        bbox: tuple,
        confidence: float,
        class_id: int,
        class_name: str,
        mask: Optional[np.ndarray] = None,
    ):
        self.bbox = bbox  # (x1, y1, x2, y2)
        self.confidence = confidence
        self.class_id = class_id
        self.class_name = class_name
        self.mask = mask

    @property
    def width_px(self) -> float:
        return self.bbox[2] - self.bbox[0]

    @property
    def height_px(self) -> float:
        return self.bbox[3] - self.bbox[1]

    @property
    def area_px(self) -> float:
        return self.width_px * self.height_px

    def to_dict(self):
        return {
            "bbox": list(self.bbox),
            "confidence": round(self.confidence, 4),
            "class_id": self.class_id,
            "class_name": self.class_name,
            "width_px": self.width_px,
            "height_px": self.height_px,
            "area_px": self.area_px,
        }


class CVPipeline:
    """
    Computer Vision pipeline for pothole detection using YOLOv8.
    Falls back to mock detection when model/dependencies not available.
    """

    DEFAULT_CLASSES = {0: "pothole", 1: "crack", 2: "road_damage"}

    def __init__(self, model_path: Optional[str] = None, confidence: float = 0.5, iou: float = 0.45):
        self.model_path = model_path
        self.confidence = confidence
        self.iou = iou
        self.model = None
        self._load_model()

    def _load_model(self):
        if not CV_AVAILABLE:
            logger.info("CV libraries not available; using mock pipeline.")
            return
        if self.model_path and Path(self.model_path).exists():
            try:
                self.model = YOLO(self.model_path)
                logger.info(f"Loaded YOLO model from {self.model_path}")
            except Exception as exc:
                logger.warning(f"Failed to load model: {exc}; using mock pipeline.")
        else:
            try:
                self.model = YOLO("yolov8n.pt")
                logger.info("Loaded default YOLOv8n model.")
            except Exception as exc:
                logger.warning(f"Could not load default model: {exc}; using mock pipeline.")

    def detect(self, image_bytes: bytes) -> list[DetectionResult]:
        """Run detection on raw image bytes."""
        if self.model is None:
            return self._mock_detect(image_bytes)

        try:
            import cv2
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Could not decode image.")
            return self._run_yolo(img)
        except Exception as exc:
            logger.error(f"Detection error: {exc}; falling back to mock.")
            return self._mock_detect(image_bytes)

    def _run_yolo(self, img: np.ndarray) -> list[DetectionResult]:
        results_list = self.model(img, conf=self.confidence, iou=self.iou, verbose=False)
        detections = []
        for r in results_list:
            boxes = r.boxes
            masks = r.masks
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                name = self.model.names.get(cls, "pothole")
                mask = None
                if masks is not None and i < len(masks.data):
                    mask = masks.data[i].cpu().numpy()
                detections.append(DetectionResult(
                    bbox=(x1, y1, x2, y2),
                    confidence=conf,
                    class_id=cls,
                    class_name=name,
                    mask=mask,
                ))
        return detections

    def _mock_detect(self, image_bytes: bytes) -> list[DetectionResult]:
        """Generate mock detection results for testing/demo."""
        import random
        rng = random.Random(len(image_bytes))
        num = rng.randint(1, 4)
        results = []
        for _ in range(num):
            x1 = rng.uniform(50, 400)
            y1 = rng.uniform(50, 300)
            x2 = x1 + rng.uniform(30, 150)
            y2 = y1 + rng.uniform(20, 100)
            conf = rng.uniform(0.55, 0.97)
            results.append(DetectionResult(
                bbox=(x1, y1, x2, y2),
                confidence=conf,
                class_id=0,
                class_name="pothole",
            ))
        return results

    def annotate_image(self, image_bytes: bytes, detections: list[DetectionResult]) -> bytes:
        """Draw bounding boxes on the image and return annotated bytes."""
        if not CV_AVAILABLE:
            return image_bytes
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return image_bytes
        for det in detections:
            x1, y1, x2, y2 = [int(v) for v in det.bbox]
            color = (0, 0, 255) if det.class_name == "pothole" else (0, 165, 255)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            label = f"{det.class_name} {det.confidence:.2f}"
            cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        _, buf = cv2.imencode(".jpg", img)
        return buf.tobytes()

    def save_image(self, image_bytes: bytes, directory: str, filename: Optional[str] = None) -> str:
        """Save image bytes to disk, return relative path."""
        os.makedirs(directory, exist_ok=True)
        if filename is None:
            filename = f"{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(directory, filename)
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        return filepath


_pipeline: Optional[CVPipeline] = None


def get_cv_pipeline() -> CVPipeline:
    global _pipeline
    if _pipeline is None:
        from app.config import settings
        _pipeline = CVPipeline(
            model_path=settings.MODEL_PATH,
            confidence=settings.MODEL_CONFIDENCE,
            iou=settings.MODEL_IOU,
        )
    return _pipeline
