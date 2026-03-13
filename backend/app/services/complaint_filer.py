"""
Automated Complaint Filing Service.
Integrates with government grievance portals (mock implementation).
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models.pothole import Pothole, PotholeStatus
from app.models.complaint import Complaint, ComplaintStatus, PortalType

logger = logging.getLogger(__name__)


class ComplaintFiler:
    """
    Files complaints on behalf of the system to government grievance portals.
    Currently implements a mock portal; real portal integrations can be plugged in.
    """

    def file_complaint(self, db: Session, pothole: Pothole) -> Complaint:
        """
        File a complaint for a given pothole.
        Returns the created Complaint record.
        """
        # Build form data
        form_data = self._build_form_data(pothole)

        # Choose portal based on state/availability
        portal = self._select_portal(pothole)

        # Submit to portal (mock)
        portal_response, complaint_id = self._submit_to_portal(portal, form_data)

        # Create complaint record
        complaint = Complaint(
            pothole_id=pothole.id,
            portal=portal,
            complaint_id=complaint_id,
            status=ComplaintStatus.FILED,
            form_data=form_data,
            portal_response=portal_response,
            filed_at=datetime.now(timezone.utc),
            escalation_level=0,
        )
        db.add(complaint)

        # Update pothole status
        pothole.status = PotholeStatus.COMPLAINT_FILED
        pothole.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(complaint)
        logger.info(f"Filed complaint {complaint.complaint_id} for pothole {pothole.id}")
        return complaint

    def _build_form_data(self, pothole: Pothole) -> dict:
        return {
            "pothole_id": pothole.id,
            "location": {
                "latitude": pothole.latitude,
                "longitude": pothole.longitude,
                "address": pothole.address or "Unknown",
                "road_name": pothole.road_name or "Unknown Highway",
                "highway_name": pothole.highway_name,
                "km_marker": pothole.km_marker,
                "state": pothole.state or "Unknown",
                "district": pothole.district or "Unknown",
            },
            "severity": pothole.severity.value if pothole.severity else "moderate",
            "dimensions": {
                "length_cm": pothole.length_cm,
                "width_cm": pothole.width_cm,
                "depth_cm": pothole.depth_cm,
                "area_sqm": pothole.area_sqm,
            },
            "evidence": {
                "image_url": pothole.image_url,
                "timestamp": pothole.detected_at.isoformat() if pothole.detected_at else None,
                "source_type": pothole.source_type or "unknown",
                "detection_confidence": pothole.confidence_score,
            },
            "complainant": {
                "name": "Autonomous Pothole Intelligence System",
                "type": "automated",
                "contact": "system@pothole-ai.gov.in",
            },
            "complaint_text": self._generate_complaint_text(pothole),
        }

    def _generate_complaint_text(self, pothole: Pothole) -> str:
        severity_desc = {
            "minor": "minor surface crack",
            "moderate": "moderate pothole",
            "severe": "severe pothole posing immediate hazard",
        }
        sev = pothole.severity.value if pothole.severity else "moderate"
        desc = severity_desc.get(sev, "pothole")
        location_str = pothole.address or f"Lat:{pothole.latitude:.4f}, Lon:{pothole.longitude:.4f}"
        text = (
            f"This is an automated complaint filed by the Autonomous Pothole Intelligence System. "
            f"A {desc} has been detected at {location_str}. "
        )
        if pothole.road_name:
            text += f"Road: {pothole.road_name}. "
        if pothole.depth_cm:
            text += f"Estimated depth: {pothole.depth_cm:.1f} cm. "
        if pothole.area_sqm:
            text += f"Approximate area: {pothole.area_sqm:.2f} m². "
        text += "Immediate repair is requested to prevent accidents and vehicle damage."
        return text

    def _select_portal(self, pothole: Pothole) -> PortalType:
        # State-specific portals first, fall back to PG Portal
        state_portals = {
            "Chhattisgarh": PortalType.STATE_PORTAL,
            "Maharashtra": PortalType.STATE_PORTAL,
            "Delhi": PortalType.MUNICIPAL,
        }
        if pothole.state and pothole.state in state_portals:
            return state_portals[pothole.state]
        return PortalType.MOCK

    def _submit_to_portal(self, portal: PortalType, form_data: dict) -> tuple[dict, str]:
        """Mock portal submission. Returns (response_dict, tracking_id)."""
        tracking_id = f"MOCK-{uuid.uuid4().hex[:10].upper()}"
        response = {
            "success": True,
            "tracking_id": tracking_id,
            "portal": portal.value,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "estimated_resolution_days": 14,
            "acknowledgement": f"Your complaint has been registered. Tracking ID: {tracking_id}",
        }
        logger.info(f"Mock portal submission successful. Tracking ID: {tracking_id}")
        return response, tracking_id


_filer: Optional[ComplaintFiler] = None


def get_complaint_filer() -> ComplaintFiler:
    global _filer
    if _filer is None:
        _filer = ComplaintFiler()
    return _filer
