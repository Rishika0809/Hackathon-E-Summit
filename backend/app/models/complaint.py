import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class ComplaintStatus(str, enum.Enum):
    PENDING = "pending"
    FILED = "filed"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED_L1 = "escalated_l1"
    ESCALATED_L2 = "escalated_l2"
    PUBLICLY_FLAGGED = "publicly_flagged"
    FAILED = "failed"


class PortalType(str, enum.Enum):
    PG_PORTAL = "pg_portal"
    STATE_PORTAL = "state_portal"
    MUNICIPAL = "municipal"
    MOCK = "mock"


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    pothole_id = Column(Integer, ForeignKey("potholes.id"), nullable=False)
    portal = Column(Enum(PortalType), nullable=False, default=PortalType.MOCK)
    complaint_id = Column(String(100), nullable=True, unique=True)  # from portal
    status = Column(Enum(ComplaintStatus), nullable=False, default=ComplaintStatus.PENDING)

    # Form data submitted
    form_data = Column(JSON, nullable=True)
    portal_response = Column(JSON, nullable=True)

    # Tracking
    filed_at = Column(DateTime, nullable=True)
    last_checked = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Escalation tracking
    escalation_level = Column(Integer, default=0)
    escalated_at = Column(DateTime, nullable=True)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    pothole = relationship("Pothole", back_populates="complaints")
    resolutions = relationship("Resolution", back_populates="complaint", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "pothole_id": self.pothole_id,
            "portal": self.portal.value if self.portal else None,
            "complaint_id": self.complaint_id,
            "status": self.status.value if self.status else None,
            "form_data": self.form_data,
            "portal_response": self.portal_response,
            "filed_at": self.filed_at.isoformat() if self.filed_at else None,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "escalation_level": self.escalation_level,
            "escalated_at": self.escalated_at.isoformat() if self.escalated_at else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
