"""
Image processing utilities for the pothole detection pipeline.
"""
import io
import os
import logging
import uuid
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ExifTags
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False


def resize_image(image_bytes: bytes, max_size: int = 1280) -> bytes:
    """Resize image to have max dimension of max_size, preserving aspect ratio."""
    if not PIL_AVAILABLE:
        return image_bytes
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail((max_size, max_size), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()
    except Exception as e:
        logger.error(f"Image resize failed: {e}")
        return image_bytes


def extract_exif_gps(image_bytes: bytes) -> Optional[Tuple[float, float]]:
    """Extract GPS coordinates from EXIF data. Returns (lat, lon) or None."""
    if not PIL_AVAILABLE:
        return None
    try:
        img = Image.open(io.BytesIO(image_bytes))
        exif_data = img._getexif()
        if not exif_data:
            return None
        gps_info = {}
        for tag, value in exif_data.items():
            tag_name = ExifTags.TAGS.get(tag, tag)
            if tag_name == "GPSInfo":
                for gps_tag, gps_val in value.items():
                    gps_name = ExifTags.GPSTAGS.get(gps_tag, gps_tag)
                    gps_info[gps_name] = gps_val
        if not gps_info:
            return None
        lat = _dms_to_decimal(gps_info.get("GPSLatitude"), gps_info.get("GPSLatitudeRef", "N"))
        lon = _dms_to_decimal(gps_info.get("GPSLongitude"), gps_info.get("GPSLongitudeRef", "E"))
        if lat and lon:
            return lat, lon
    except Exception as e:
        logger.debug(f"EXIF extraction failed: {e}")
    return None


def _dms_to_decimal(dms, ref: str) -> Optional[float]:
    """Convert degrees/minutes/seconds to decimal degrees."""
    if dms is None:
        return None
    try:
        d, m, s = float(dms[0]), float(dms[1]), float(dms[2])
        decimal = d + m / 60 + s / 3600
        if ref in ("S", "W"):
            decimal = -decimal
        return decimal
    except Exception:
        return None


def create_thumbnail(image_bytes: bytes, size: Tuple[int, int] = (200, 200)) -> bytes:
    """Create a thumbnail from image bytes."""
    if not PIL_AVAILABLE:
        return image_bytes
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail(size, Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        return buf.getvalue()
    except Exception as e:
        logger.error(f"Thumbnail creation failed: {e}")
        return image_bytes


def validate_image(image_bytes: bytes) -> bool:
    """Check that image_bytes is a valid image."""
    if not PIL_AVAILABLE:
        return len(image_bytes) > 100
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        return True
    except Exception:
        return False


def compute_image_hash(image_bytes: bytes) -> str:
    """Compute a simple hash for deduplication."""
    import hashlib
    return hashlib.sha256(image_bytes).hexdigest()[:16]


def save_upload(image_bytes: bytes, upload_dir: str, prefix: str = "img") -> Tuple[str, str]:
    """
    Save image and thumbnail to upload_dir.
    Returns (image_path, thumbnail_path).
    """
    os.makedirs(upload_dir, exist_ok=True)
    thumb_dir = os.path.join(upload_dir, "thumbnails")
    os.makedirs(thumb_dir, exist_ok=True)

    uid = uuid.uuid4().hex[:12]
    img_filename = f"{prefix}_{uid}.jpg"
    thumb_filename = f"{prefix}_{uid}_thumb.jpg"

    img_path = os.path.join(upload_dir, img_filename)
    thumb_path = os.path.join(thumb_dir, thumb_filename)

    with open(img_path, "wb") as f:
        f.write(image_bytes)

    thumb_bytes = create_thumbnail(image_bytes)
    with open(thumb_path, "wb") as f:
        f.write(thumb_bytes)

    return img_path, thumb_path
