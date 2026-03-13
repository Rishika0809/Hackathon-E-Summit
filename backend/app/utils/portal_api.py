"""
Mock Government Portal API client.
Simulates integration with PG Portal and state grievance systems.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class PortalAPIClient:
    """
    Thin wrapper around government grievance portal APIs.
    Implements mock responses for all portals.
    """

    def submit_complaint(
        self,
        portal_url: str,
        api_key: str,
        form_data: dict,
    ) -> dict:
        """Submit a complaint to a portal. Returns portal response."""
        # Mock implementation — replace with actual HTTP calls when API is available
        tracking_id = f"PGPORTAL-{uuid.uuid4().hex[:8].upper()}"
        return {
            "success": True,
            "tracking_id": tracking_id,
            "status": "filed",
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "expected_resolution": "14 days",
            "portal_url": f"{portal_url}/track/{tracking_id}",
        }

    def check_status(self, portal_url: str, api_key: str, tracking_id: str) -> dict:
        """Poll a portal for the current status of a complaint."""
        import random
        statuses = ["filed", "acknowledged", "in_progress", "resolved"]
        status = random.choice(statuses)
        return {
            "tracking_id": tracking_id,
            "status": status,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "remarks": f"Complaint is currently {status}.",
        }

    def upload_evidence(self, portal_url: str, api_key: str, tracking_id: str, image_bytes: bytes) -> dict:
        """Upload image evidence to the portal."""
        mock_url = f"{portal_url}/evidence/{tracking_id}/{uuid.uuid4().hex[:8]}.jpg"
        return {
            "success": True,
            "evidence_url": mock_url,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }

    def escalate_complaint(self, portal_url: str, api_key: str, tracking_id: str, level: int) -> dict:
        """Escalate a complaint to higher authority."""
        return {
            "success": True,
            "tracking_id": tracking_id,
            "escalation_level": level,
            "escalated_at": datetime.now(timezone.utc).isoformat(),
            "escalated_to": "District Collector" if level == 1 else "State PWD Secretary",
        }


_client: Optional[PortalAPIClient] = None


def get_portal_client() -> PortalAPIClient:
    global _client
    if _client is None:
        _client = PortalAPIClient()
    return _client
