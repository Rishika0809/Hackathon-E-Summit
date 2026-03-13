"""
Detection API — upload images for pothole detection.
"""
import os
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.models.pothole import Pothole, SeverityLevel, PotholeStatus
from app.services.cv_pipeline import get_cv_pipeline
from app.services.severity_classifier import get_severity_classifier
from app.services.risk_analyzer import get_risk_analyzer
from app.utils.geolocation import get_geo_locator
from app.utils.image_processor import resize_image, extract_exif_gps, save_upload, validate_image
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/detect", tags=["Detection"])


@router.post("/", summary="Upload image for pothole detection")
async def detect_potholes(
    file: UploadFile = File(..., description="Road image (JPEG/PNG)"),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    source_type: str = Form("dashcam", description="satellite | drone | dashcam"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    """
    Upload a road image for pothole detection.
    Returns list of detected potholes with severity and location info.
    """
    image_bytes = await file.read()

    if not validate_image(image_bytes):
        raise HTTPException(status_code=400, detail="Invalid image file.")

    if len(image_bytes) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="Image too large. Max 10 MB.")

    # Resize for processing
    image_bytes = resize_image(image_bytes)

    # Try to extract GPS from EXIF
    if latitude is None or longitude is None:
        gps = extract_exif_gps(image_bytes)
        if gps:
            latitude, longitude = gps
        else:
            latitude = latitude or 20.5937   # default: India center
            longitude = longitude or 78.9629

    # Save upload
    img_path, thumb_path = save_upload(image_bytes, settings.UPLOAD_DIR, prefix="detect")

    # Run detection
    pipeline = get_cv_pipeline()
    detections = pipeline.detect(image_bytes)

    if not detections:
        return JSONResponse({
            "detected": False,
            "message": "No potholes detected in the image.",
            "potholes": [],
        })

    # Classify each detection and save to DB
    classifier = get_severity_classifier()
    risk_analyzer = get_risk_analyzer()
    geo = get_geo_locator()

    geo_info = geo.reverse_geocode(latitude, longitude)
    saved_potholes = []

    for det in detections:
        sev_result = classifier.classify(
            width_px=det.width_px,
            height_px=det.height_px,
            confidence=det.confidence,
            source_type=source_type,
        )
        risk_result = risk_analyzer.compute_risk(severity=sev_result.severity)

        pothole = Pothole(
            latitude=latitude,
            longitude=longitude,
            severity=sev_result.severity,
            status=PotholeStatus.CLASSIFIED,
            length_cm=sev_result.length_cm,
            width_cm=sev_result.width_cm,
            depth_cm=sev_result.depth_cm,
            area_sqm=sev_result.area_sqm,
            road_name=geo_info.road_name,
            highway_name=geo_info.highway_name,
            km_marker=geo_info.km_marker,
            address=geo_info.address,
            state=geo_info.state,
            district=geo_info.district,
            image_url=img_path,
            thumbnail_url=thumb_path,
            source_type=source_type,
            confidence_score=det.confidence,
            detection_model="YOLOv8",
            risk_score=risk_result.total_score,
            detected_at=datetime.now(timezone.utc),
        )
        db.add(pothole)
        db.flush()
        saved_potholes.append(pothole)

    db.commit()

    return {
        "detected": True,
        "count": len(saved_potholes),
        "potholes": [p.to_dict() for p in saved_potholes],
        "image_path": img_path,
    }


@router.post("/batch", summary="Batch process multiple images")
async def detect_batch(
    files: list[UploadFile] = File(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    source_type: str = Form("drone"),
    db: Session = Depends(get_db),
):
    """Process multiple images in batch mode."""
    results = []
    for f in files:
        image_bytes = await f.read()
        if not validate_image(image_bytes):
            results.append({"filename": f.filename, "error": "Invalid image"})
            continue
        image_bytes = resize_image(image_bytes)
        pipeline = get_cv_pipeline()
        detections = pipeline.detect(image_bytes)
        results.append({
            "filename": f.filename,
            "detections": [d.to_dict() for d in detections],
        })
    return {"batch_results": results, "total_files": len(files)}
