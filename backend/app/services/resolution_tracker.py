"""
Resolution Tracking Service.
Monitors complaints, verifies repairs, and escalates unresolved issues.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.complaint import Complaint, ComplaintStatus
from app.models.pothole import Pothole, PotholeStatus
from app.models.resolution import Resolution
from app.config import settings

logger = logging.getLogger(__name__)


class ResolutionTracker:
    """
    Polls complaint statuses, verifies repairs via re-scan,
    and escalates complaints that remain unresolved.
    """

    def check_and_escalate(self, db: Session) -> dict:
        """
        Main loop: check all open complaints and escalate if needed.
        Returns a summary of actions taken.
        """
        now = datetime.now(timezone.utc)
        summary = {"checked": 0, "escalated_l1": 0, "escalated_l2": 0, "flagged": 0, "closed": 0}

        open_statuses = [
            ComplaintStatus.FILED,
            ComplaintStatus.ACKNOWLEDGED,
            ComplaintStatus.IN_PROGRESS,
            ComplaintStatus.ESCALATED_L1,
        ]
        complaints = db.query(Complaint).filter(Complaint.status.in_(open_statuses)).all()

        for complaint in complaints:
            summary["checked"] += 1
            filed_at = complaint.filed_at or complaint.created_at
            days_open = (now - filed_at).days

            if days_open >= settings.PUBLIC_FLAG_DAYS and complaint.status != ComplaintStatus.PUBLICLY_FLAGGED:
                self._flag_public(db, complaint, now)
                summary["flagged"] += 1
            elif days_open >= settings.SECOND_ESCALATION_DAYS and complaint.escalation_level < 2:
                self._escalate(db, complaint, level=2, now=now)
                summary["escalated_l2"] += 1
            elif days_open >= settings.FIRST_ESCALATION_DAYS and complaint.escalation_level < 1:
                self._escalate(db, complaint, level=1, now=now)
                summary["escalated_l1"] += 1

            complaint.last_checked = now

        db.commit()
        return summary

    def _escalate(self, db: Session, complaint: Complaint, level: int, now: datetime):
        complaint.escalation_level = level
        complaint.escalated_at = now
        if level == 1:
            complaint.status = ComplaintStatus.ESCALATED_L1
            complaint.notes = (
                (complaint.notes or "") +
                f"\n[{now.date()}] Escalated to Level 1 (First Escalation after {settings.FIRST_ESCALATION_DAYS} days)."
            )
        elif level == 2:
            complaint.status = ComplaintStatus.ESCALATED_L2
            complaint.notes = (
                (complaint.notes or "") +
                f"\n[{now.date()}] Escalated to Level 2 (Higher Authority after {settings.SECOND_ESCALATION_DAYS} days)."
            )
        logger.info(f"Complaint {complaint.id} escalated to level {level}")

    def _flag_public(self, db: Session, complaint: Complaint, now: datetime):
        complaint.status = ComplaintStatus.PUBLICLY_FLAGGED
        complaint.notes = (
            (complaint.notes or "") +
            f"\n[{now.date()}] Publicly flagged on dashboard after {settings.PUBLIC_FLAG_DAYS} days without resolution."
        )
        # Update pothole status
        pothole = db.query(Pothole).filter(Pothole.id == complaint.pothole_id).first()
        if pothole:
            pothole.status = PotholeStatus.ESCALATED
        logger.warning(f"Complaint {complaint.id} publicly flagged")

    def verify_resolution(
        self,
        db: Session,
        complaint_id: int,
        verification_image_bytes: Optional[bytes] = None,
        verification_image_url: Optional[str] = None,
    ) -> Resolution:
        """
        Verify that a pothole has been repaired.
        Compares before/after images if available.
        """
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            raise ValueError(f"Complaint {complaint_id} not found")

        pothole = db.query(Pothole).filter(Pothole.id == complaint.pothole_id).first()

        # Compute similarity score (mock: assume partial repair)
        similarity_score = self._compute_similarity(
            pothole.image_url if pothole else None,
            verification_image_url,
        )

        pothole_still_present = similarity_score < 0.85
        repair_quality = self._assess_repair_quality(similarity_score)

        resolution = Resolution(
            complaint_id=complaint_id,
            resolved_at=datetime.now(timezone.utc) if not pothole_still_present else None,
            verified_at=datetime.now(timezone.utc),
            verification_image_url=verification_image_url,
            before_image_url=pothole.image_url if pothole else None,
            after_image_url=verification_image_url,
            similarity_score=similarity_score,
            repair_quality=repair_quality,
            is_verified=not pothole_still_present,
            verified_by="system",
            pothole_still_present=pothole_still_present,
        )
        db.add(resolution)

        if not pothole_still_present:
            complaint.status = ComplaintStatus.RESOLVED
            complaint.resolved_at = datetime.now(timezone.utc)
            if pothole:
                pothole.status = PotholeStatus.VERIFIED
        else:
            complaint.notes = (
                (complaint.notes or "") +
                f"\n[{datetime.now(timezone.utc).date()}] Re-scan shows pothole still present (similarity={similarity_score:.2f})."
            )

        db.commit()
        db.refresh(resolution)
        return resolution

    def _compute_similarity(
        self, before_url: Optional[str], after_url: Optional[str]
    ) -> float:
        """
        Compute image similarity between before and after images.
        Mock implementation returns a plausible score.
        """
        if not before_url or not after_url:
            return 0.75  # assume partial repair
        # In production: use structural similarity (SSIM) or feature matching
        return 0.90  # mock: road repaired

    def _assess_repair_quality(self, similarity_score: float) -> str:
        if similarity_score >= 0.90:
            return "good"
        elif similarity_score >= 0.70:
            return "partial"
        else:
            return "poor"

    def poll_portal_status(self, db: Session, complaint: Complaint) -> ComplaintStatus:
        """
        Poll the government portal for the latest complaint status.
        Mock implementation.
        """
        # In production: call the actual portal API
        import random
        statuses = [ComplaintStatus.ACKNOWLEDGED, ComplaintStatus.IN_PROGRESS, ComplaintStatus.FILED]
        new_status = random.choice(statuses)
        if complaint.status != new_status:
            complaint.status = new_status
            complaint.last_checked = datetime.now(timezone.utc)
            db.commit()
        return complaint.status


_tracker: Optional[ResolutionTracker] = None


def get_resolution_tracker() -> ResolutionTracker:
    global _tracker
    if _tracker is None:
        _tracker = ResolutionTracker()
    return _tracker
