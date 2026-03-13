from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Resolution(Base):
    __tablename__ = "resolutions"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)

    # Verification
    resolved_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_image_url = Column(String(500), nullable=True)

    # Comparison metrics
    before_image_url = Column(String(500), nullable=True)
    after_image_url = Column(String(500), nullable=True)
    similarity_score = Column(Float, nullable=True)  # 0-1, how similar before/after
    repair_quality = Column(String(50), nullable=True)  # good, partial, poor

    # Verification result
    is_verified = Column(Boolean, default=False)
    verification_notes = Column(Text, nullable=True)
    verified_by = Column(String(100), nullable=True)  # system or user

    # Re-scan data
    rescan_latitude = Column(Float, nullable=True)
    rescan_longitude = Column(Float, nullable=True)
    pothole_still_present = Column(Boolean, nullable=True)
    pothole_depth_after = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    complaint = relationship("Complaint", back_populates="resolutions")

    def to_dict(self):
        return {
            "id": self.id,
            "complaint_id": self.complaint_id,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "verification_image_url": self.verification_image_url,
            "before_image_url": self.before_image_url,
            "after_image_url": self.after_image_url,
            "similarity_score": self.similarity_score,
            "repair_quality": self.repair_quality,
            "is_verified": self.is_verified,
            "verification_notes": self.verification_notes,
            "verified_by": self.verified_by,
            "pothole_still_present": self.pothole_still_present,
            "pothole_depth_after": self.pothole_depth_after,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
