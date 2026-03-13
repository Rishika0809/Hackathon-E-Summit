import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class SeverityLevel(str, enum.Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"


class PotholeStatus(str, enum.Enum):
    DETECTED = "detected"
    CLASSIFIED = "classified"
    COMPLAINT_FILED = "complaint_filed"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    VERIFIED = "verified"
    ESCALATED = "escalated"


class Pothole(Base):
    __tablename__ = "potholes"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    severity = Column(Enum(SeverityLevel), nullable=False, default=SeverityLevel.MODERATE)
    status = Column(Enum(PotholeStatus), nullable=False, default=PotholeStatus.DETECTED)

    # Dimensions
    length_cm = Column(Float, nullable=True)
    width_cm = Column(Float, nullable=True)
    depth_cm = Column(Float, nullable=True)
    area_sqm = Column(Float, nullable=True)

    # Location details
    road_name = Column(String(255), nullable=True)
    highway_name = Column(String(255), nullable=True)
    km_marker = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    state = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)

    # Image info
    image_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    source_type = Column(String(50), nullable=True)  # satellite, drone, dashcam

    # Detection metadata
    confidence_score = Column(Float, nullable=True)
    detection_model = Column(String(100), nullable=True)
    risk_score = Column(Float, nullable=True)
    priority_rank = Column(Integer, nullable=True)

    # Timestamps
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    complaints = relationship("Complaint", back_populates="pothole", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "severity": self.severity.value if self.severity else None,
            "status": self.status.value if self.status else None,
            "length_cm": self.length_cm,
            "width_cm": self.width_cm,
            "depth_cm": self.depth_cm,
            "area_sqm": self.area_sqm,
            "road_name": self.road_name,
            "highway_name": self.highway_name,
            "km_marker": self.km_marker,
            "address": self.address,
            "state": self.state,
            "district": self.district,
            "image_url": self.image_url,
            "thumbnail_url": self.thumbnail_url,
            "source_type": self.source_type,
            "confidence_score": self.confidence_score,
            "risk_score": self.risk_score,
            "priority_rank": self.priority_rank,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
