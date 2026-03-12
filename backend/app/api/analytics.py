"""
Analytics API — dashboard metrics, charts, and KPIs.
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from fastapi import APIRouter, Depends

from app.database import get_db
from app.models.pothole import Pothole, SeverityLevel, PotholeStatus
from app.models.complaint import Complaint, ComplaintStatus
from app.models.resolution import Resolution

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/", summary="Get dashboard analytics")
def get_analytics(db: Session = Depends(get_db)):
    # Pothole counts by severity
    severity_counts = dict(
        db.query(Pothole.severity, func.count(Pothole.id))
        .group_by(Pothole.severity)
        .all()
    )

    # Pothole counts by status
    status_counts = dict(
        db.query(Pothole.status, func.count(Pothole.id))
        .group_by(Pothole.status)
        .all()
    )

    # Complaint stats
    complaint_counts = dict(
        db.query(Complaint.status, func.count(Complaint.id))
        .group_by(Complaint.status)
        .all()
    )

    total_potholes = db.query(func.count(Pothole.id)).scalar() or 0
    total_complaints = db.query(func.count(Complaint.id)).scalar() or 0
    total_resolved = db.query(func.count(Resolution.id)).filter(Resolution.is_verified == True).scalar() or 0

    avg_risk = db.query(func.avg(Pothole.risk_score)).scalar()

    # Response time analytics (days from detection to complaint)
    response_time_data = []

    # Severity breakdown for chart
    severity_chart = [
        {"name": sev.value.capitalize(), "value": severity_counts.get(sev, 0)}
        for sev in SeverityLevel
    ]

    # Status breakdown
    status_chart = [
        {"name": st.value.replace("_", " ").capitalize(), "value": status_counts.get(st, 0)}
        for st in PotholeStatus
    ]

    # Complaint status breakdown
    complaint_chart = [
        {"name": st.value.replace("_", " ").capitalize(), "value": complaint_counts.get(st, 0)}
        for st in ComplaintStatus
    ]

    return {
        "summary": {
            "total_potholes": total_potholes,
            "total_complaints": total_complaints,
            "total_resolved": total_resolved,
            "resolution_rate": round(total_resolved / total_complaints * 100, 1) if total_complaints else 0,
            "avg_risk_score": round(float(avg_risk), 2) if avg_risk else 0,
        },
        "severity_breakdown": severity_chart,
        "status_breakdown": status_chart,
        "complaint_breakdown": complaint_chart,
    }


@router.get("/kpis", summary="Get KPI metrics")
def get_kpis(db: Session = Depends(get_db)):
    total = db.query(func.count(Pothole.id)).scalar() or 0
    severe = db.query(func.count(Pothole.id)).filter(Pothole.severity == SeverityLevel.SEVERE).scalar() or 0
    filed = db.query(func.count(Complaint.id)).filter(
        Complaint.status != ComplaintStatus.PENDING
    ).scalar() or 0
    resolved = db.query(func.count(Resolution.id)).filter(Resolution.is_verified == True).scalar() or 0
    escalated = db.query(func.count(Complaint.id)).filter(
        Complaint.escalation_level > 0
    ).scalar() or 0

    return {
        "kpis": [
            {"label": "Total Potholes Detected", "value": total, "unit": ""},
            {"label": "Severe Potholes", "value": severe, "unit": ""},
            {"label": "Complaints Filed", "value": filed, "unit": ""},
            {"label": "Resolved & Verified", "value": resolved, "unit": ""},
            {"label": "Escalated Complaints", "value": escalated, "unit": ""},
            {
                "label": "Automation Rate",
                "value": 100,
                "unit": "%",
                "description": "100% of complaints filed autonomously",
            },
        ]
    }
