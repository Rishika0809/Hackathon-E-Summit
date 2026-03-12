"""
Monitoring API — pothole list, details, and status updates.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pothole import Pothole, SeverityLevel, PotholeStatus
from app.services.risk_analyzer import get_risk_analyzer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/potholes", tags=["Potholes"])


@router.get("/", summary="List all detected potholes")
def list_potholes(
    severity: Optional[str] = Query(None, description="Filter by severity: minor|moderate|severe"),
    status: Optional[str] = Query(None, description="Filter by status"),
    state: Optional[str] = Query(None),
    min_risk: Optional[float] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(Pothole)
    if severity:
        try:
            sev_enum = SeverityLevel(severity)
            q = q.filter(Pothole.severity == sev_enum)
        except ValueError:
            raise HTTPException(400, f"Invalid severity: {severity}")
    if status:
        try:
            st_enum = PotholeStatus(status)
            q = q.filter(Pothole.status == st_enum)
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")
    if state:
        q = q.filter(Pothole.state.ilike(f"%{state}%"))
    if min_risk is not None:
        q = q.filter(Pothole.risk_score >= min_risk)
    total = q.count()
    potholes = q.order_by(Pothole.risk_score.desc().nullslast()).offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "potholes": [p.to_dict() for p in potholes],
    }


@router.get("/{pothole_id}", summary="Get pothole details")
def get_pothole(pothole_id: int, db: Session = Depends(get_db)):
    p = db.query(Pothole).filter(Pothole.id == pothole_id).first()
    if not p:
        raise HTTPException(404, "Pothole not found.")
    data = p.to_dict()
    data["complaints"] = [c.to_dict() for c in p.complaints]
    return data


@router.get("/heatmap/data", summary="Get risk heat map data")
def get_heatmap(db: Session = Depends(get_db)):
    potholes = db.query(Pothole).all()
    analyzer = get_risk_analyzer()
    points = analyzer.generate_heatmap_points(potholes)
    return {"points": points, "total": len(points)}


@router.get("/priority/queue", summary="Get prioritized pothole queue")
def get_priority_queue(db: Session = Depends(get_db)):
    potholes = db.query(Pothole).filter(
        Pothole.status.in_([PotholeStatus.DETECTED, PotholeStatus.CLASSIFIED])
    ).all()
    analyzer = get_risk_analyzer()
    prioritized = analyzer.build_priority_queue(potholes)
    return {
        "total": len(prioritized),
        "queue": [p.to_dict() for p in prioritized],
    }
