"""
Severity classification for detected potholes.
Classifies based on pixel dimensions and optional depth estimation.
"""
import logging
from dataclasses import dataclass
from typing import Optional

from app.models.pothole import SeverityLevel

logger = logging.getLogger(__name__)


# Pixel-to-cm conversion assumptions (calibrated for typical road camera setups)
# These can be overridden per source type
PIXEL_TO_CM = {
    "satellite": 5.0,   # 1 pixel ≈ 5 cm (50cm/pixel resolution)
    "drone": 0.5,        # 1 pixel ≈ 0.5 cm
    "dashcam": 0.3,      # 1 pixel ≈ 0.3 cm
    "default": 1.0,
}


@dataclass
class SeverityResult:
    severity: SeverityLevel
    depth_cm: float
    length_cm: float
    width_cm: float
    area_sqm: float
    confidence: float
    reason: str


class SeverityClassifier:
    """
    Classifies pothole severity based on:
    - Pixel dimensions from bounding box
    - Source type (satellite/drone/dashcam)
    - Optional model-based depth estimation
    """

    DEPTH_THRESHOLDS = {
        "minor": (0, 5),       # < 5 cm
        "moderate": (5, 15),   # 5–15 cm
        "severe": (15, 999),   # > 15 cm
    }

    def classify(
        self,
        width_px: float,
        height_px: float,
        confidence: float,
        source_type: str = "default",
        estimated_depth_cm: Optional[float] = None,
    ) -> SeverityResult:
        scale = PIXEL_TO_CM.get(source_type, PIXEL_TO_CM["default"])

        length_cm = width_px * scale
        width_cm = height_px * scale
        area_sqm = (length_cm / 100) * (width_cm / 100)

        # Estimate depth from area if not provided
        if estimated_depth_cm is None:
            estimated_depth_cm = self._estimate_depth(area_sqm, confidence)

        severity = self._depth_to_severity(estimated_depth_cm)
        reason = (
            f"Depth={estimated_depth_cm:.1f}cm, "
            f"Dimensions={length_cm:.1f}x{width_cm:.1f}cm, "
            f"Area={area_sqm:.3f}m²"
        )

        return SeverityResult(
            severity=severity,
            depth_cm=round(estimated_depth_cm, 2),
            length_cm=round(length_cm, 2),
            width_cm=round(width_cm, 2),
            area_sqm=round(area_sqm, 4),
            confidence=round(confidence, 4),
            reason=reason,
        )

    def _estimate_depth(self, area_sqm: float, confidence: float) -> float:
        """
        Heuristic depth estimation from visible area.
        Larger potholes tend to be deeper.
        """
        base = area_sqm * 30  # empirical factor
        # Adjust by confidence
        depth = max(1.0, min(base * confidence, 50.0))
        return depth

    def _depth_to_severity(self, depth_cm: float) -> SeverityLevel:
        if depth_cm < self.DEPTH_THRESHOLDS["moderate"][0]:
            return SeverityLevel.MINOR
        elif depth_cm < self.DEPTH_THRESHOLDS["severe"][0]:
            return SeverityLevel.MODERATE
        else:
            return SeverityLevel.SEVERE


_classifier: Optional[SeverityClassifier] = None


def get_severity_classifier() -> SeverityClassifier:
    global _classifier
    if _classifier is None:
        _classifier = SeverityClassifier()
    return _classifier
