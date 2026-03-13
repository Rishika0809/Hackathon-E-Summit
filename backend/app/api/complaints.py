"""
Complaints API — file and track complaints.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.pothole import Pothole
from app.models.complaint import Complaint, ComplaintStatus
from app.services.complaint_filer import get_complaint_filer
from app.services.resolution_tracker import get_resolution_tracker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/complaints", tags=["Complaints"])


class FileComplaintRequest(BaseModel):
    pothole_id: int
    notes: Optional[str] = None


@router.post("/", summary="File a complaint for a pothole")
def file_complaint(
    req: FileComplaintRequest,
    db: Session = Depends(get_db),
):
    pothole = db.query(Pothole).filter(Pothole.id == req.pothole_id).first()
    if not pothole:
        raise HTTPException(status_code=404, detail="Pothole not found.")

    filer = get_complaint_filer()
    complaint = filer.file_complaint(db, pothole)
    if req.notes:
        complaint.notes = req.notes
        db.commit()
    return complaint.to_dict()


@router.get("/", summary="List all complaints")
def list_complaints(
    status: Optional[str] = Query(None),
    pothole_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(Complaint)
    if status:
        try:
            status_enum = ComplaintStatus(status)
            q = q.filter(Complaint.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    if pothole_id:
        q = q.filter(Complaint.pothole_id == pothole_id)
    total = q.count()
    complaints = q.offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "complaints": [c.to_dict() for c in complaints],
    }


@router.get("/{complaint_id}", summary="Get complaint details")
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    return complaint.to_dict()


@router.post("/{complaint_id}/check-escalation", summary="Trigger escalation check")
def check_escalation(complaint_id: int, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    tracker = get_resolution_tracker()
    summary = tracker.check_and_escalate(db)
    return {"message": "Escalation check complete", "summary": summary}


@router.post("/{complaint_id}/verify", summary="Verify resolution of a complaint")
def verify_resolution(
    complaint_id: int,
    verification_image_url: Optional[str] = None,
    db: Session = Depends(get_db),
):
    tracker = get_resolution_tracker()
    try:
        resolution = tracker.verify_resolution(
            db,
            complaint_id=complaint_id,
            verification_image_url=verification_image_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return resolution.to_dict()


@router.post("/escalate-all", summary="Run escalation check on all open complaints")
def escalate_all(db: Session = Depends(get_db)):
    tracker = get_resolution_tracker()
    summary = tracker.check_and_escalate(db)
    return {"message": "Escalation sweep complete", "summary": summary}
