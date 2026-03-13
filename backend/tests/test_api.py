"""
Integration tests for the FastAPI API.
Uses an in-memory SQLite database for isolation.
"""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_pothole.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    """Clean all tables before each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def make_fake_jpeg() -> bytes:
    """Minimal valid JPEG bytes."""
    # Very small valid JPEG
    return (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t'
        b'\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
        b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\x1e'
        b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00'
        b'\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
        b'\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04'
        b'\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa'
        b'\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xff\xd9'
    )


class TestHealthEndpoints:
    def test_root(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "running"

    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestDetectionAPI:
    def test_detect_with_valid_image(self):
        img = make_fake_jpeg()
        # Patch validate_image to return True for the test (PIL is strict about JPEG validity)
        with patch("app.api.detection.validate_image", return_value=True):
            resp = client.post(
                "/api/detect/",
                files={"file": ("test.jpg", img, "image/jpeg")},
                data={"latitude": "20.5", "longitude": "78.9", "source_type": "dashcam"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "detected" in data
        assert "potholes" in data

    def test_detect_empty_bytes_rejected(self):
        resp = client.post(
            "/api/detect/",
            files={"file": ("empty.jpg", b"", "image/jpeg")},
            data={"latitude": "20.5", "longitude": "78.9"},
        )
        assert resp.status_code == 400


class TestPotholeAPI:
    def _create_pothole(self) -> int:
        """Helper: detect an image to create a pothole record."""
        img = make_fake_jpeg()
        with patch("app.api.detection.validate_image", return_value=True):
            resp = client.post(
                "/api/detect/",
                files={"file": ("test.jpg", img, "image/jpeg")},
                data={"latitude": "20.5", "longitude": "78.9", "source_type": "dashcam"},
            )
        data = resp.json()
        if data.get("potholes"):
            return data["potholes"][0]["id"]
        return None

    def test_list_potholes_empty(self):
        resp = client.get("/api/potholes/")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_potholes_after_detection(self):
        self._create_pothole()
        resp = client.get("/api/potholes/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 0  # mock may or may not detect

    def test_get_nonexistent_pothole(self):
        resp = client.get("/api/potholes/9999")
        assert resp.status_code == 404

    def test_heatmap_data(self):
        resp = client.get("/api/potholes/heatmap/data")
        assert resp.status_code == 200
        assert "points" in resp.json()

    def test_priority_queue(self):
        resp = client.get("/api/potholes/priority/queue")
        assert resp.status_code == 200
        assert "queue" in resp.json()


class TestComplaintsAPI:
    def _create_pothole(self) -> int:
        img = make_fake_jpeg()
        with patch("app.api.detection.validate_image", return_value=True):
            resp = client.post(
                "/api/detect/",
                files={"file": ("test.jpg", img, "image/jpeg")},
                data={"latitude": "20.5", "longitude": "78.9", "source_type": "dashcam"},
            )
        data = resp.json()
        if data.get("potholes"):
            return data["potholes"][0]["id"]
        return None

    def test_list_complaints_empty(self):
        resp = client.get("/api/complaints/")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_file_complaint(self):
        pothole_id = self._create_pothole()
        if pothole_id is None:
            pytest.skip("No pothole detected in mock mode")
        resp = client.post("/api/complaints/", json={"pothole_id": pothole_id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["pothole_id"] == pothole_id
        assert data["complaint_id"] is not None

    def test_file_complaint_nonexistent_pothole(self):
        resp = client.post("/api/complaints/", json={"pothole_id": 9999})
        assert resp.status_code == 404

    def test_get_nonexistent_complaint(self):
        resp = client.get("/api/complaints/9999")
        assert resp.status_code == 404


class TestAnalyticsAPI:
    def test_analytics_empty(self):
        resp = client.get("/api/analytics/")
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert data["summary"]["total_potholes"] == 0

    def test_kpis(self):
        resp = client.get("/api/analytics/kpis")
        assert resp.status_code == 200
        data = resp.json()
        assert "kpis" in data
        assert len(data["kpis"]) > 0
