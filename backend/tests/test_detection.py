"""
Tests for pothole detection pipeline.
"""
import pytest
from unittest.mock import patch, MagicMock


def make_fake_image_bytes(size: int = 1000) -> bytes:
    """Generate minimal JPEG-like bytes for testing."""
    return b"\xff\xd8\xff" + b"\x00" * size + b"\xff\xd9"


class TestCVPipeline:
    def test_mock_detect_returns_results(self):
        from app.services.cv_pipeline import CVPipeline
        pipeline = CVPipeline(model_path=None, confidence=0.5)
        pipeline.model = None  # force mock mode
        image_bytes = make_fake_image_bytes()
        detections = pipeline.detect(image_bytes)
        assert isinstance(detections, list)
        assert len(detections) >= 1

    def test_detection_result_properties(self):
        from app.services.cv_pipeline import DetectionResult
        det = DetectionResult(bbox=(10, 20, 110, 80), confidence=0.75, class_id=0, class_name="pothole")
        assert det.width_px == 100
        assert det.height_px == 60
        assert det.area_px == 6000

    def test_detection_result_to_dict(self):
        from app.services.cv_pipeline import DetectionResult
        det = DetectionResult(bbox=(0, 0, 50, 50), confidence=0.9, class_id=0, class_name="pothole")
        d = det.to_dict()
        assert "bbox" in d
        assert d["confidence"] == 0.9
        assert d["class_name"] == "pothole"


class TestSeverityClassifier:
    def setup_method(self):
        from app.services.severity_classifier import SeverityClassifier
        self.clf = SeverityClassifier()

    def test_minor_classification(self):
        result = self.clf.classify(width_px=10, height_px=10, confidence=0.6, source_type="dashcam")
        from app.models.pothole import SeverityLevel
        assert result.severity == SeverityLevel.MINOR

    def test_severe_classification(self):
        # Large pothole on satellite imagery
        result = self.clf.classify(width_px=500, height_px=400, confidence=0.95, source_type="satellite")
        from app.models.pothole import SeverityLevel
        assert result.severity == SeverityLevel.SEVERE

    def test_result_has_dimensions(self):
        result = self.clf.classify(width_px=100, height_px=80, confidence=0.8)
        assert result.length_cm > 0
        assert result.width_cm > 0
        assert result.area_sqm >= 0

    def test_explicit_depth_override(self):
        result = self.clf.classify(width_px=50, height_px=50, confidence=0.7, estimated_depth_cm=20.0)
        from app.models.pothole import SeverityLevel
        assert result.severity == SeverityLevel.SEVERE
        assert result.depth_cm == 20.0


class TestRiskAnalyzer:
    def setup_method(self):
        from app.services.risk_analyzer import RiskAnalyzer
        self.analyzer = RiskAnalyzer()

    def test_severe_pothole_high_risk(self):
        from app.models.pothole import SeverityLevel
        result = self.analyzer.compute_risk(
            severity=SeverityLevel.SEVERE,
            traffic_volume=3000,
            speed_limit_kmh=100,
            near_intersection=True,
        )
        assert result.total_score > 50
        assert result.priority_level in ("critical", "high")

    def test_minor_pothole_low_risk(self):
        from app.models.pothole import SeverityLevel
        result = self.analyzer.compute_risk(
            severity=SeverityLevel.MINOR,
            traffic_volume=100,
            speed_limit_kmh=40,
        )
        assert result.total_score < 60

    def test_risk_score_range(self):
        from app.models.pothole import SeverityLevel
        for sev in SeverityLevel:
            result = self.analyzer.compute_risk(severity=sev)
            assert 0 <= result.total_score <= 100

    def test_priority_levels(self):
        from app.models.pothole import SeverityLevel
        result = self.analyzer.compute_risk(
            severity=SeverityLevel.SEVERE,
            traffic_volume=5000,
            speed_limit_kmh=120,
            near_curve=True,
            near_intersection=True,
            historical_accidents=5,
        )
        assert result.priority_level == "critical"


class TestGeoLocator:
    def test_mock_geocode(self):
        from app.utils.geolocation import GeoLocator
        locator = GeoLocator()
        locator.geocoder = None  # force mock
        info = locator.reverse_geocode(21.25, 81.63)
        assert info.latitude == 21.25
        assert info.longitude == 81.63
        assert info.state is not None

    def test_haversine_distance(self):
        from app.utils.geolocation import GeoLocator
        km = GeoLocator._haversine_km(0, 0, 0, 1)
        assert 110 < km < 112  # approx 111 km per degree at equator
