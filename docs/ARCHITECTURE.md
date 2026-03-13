# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Sources                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│  │ Satellite│  │  Drone   │  │ Dashcam  │                       │
│  │ Imagery  │  │ Footage  │  │  Feeds   │                       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                       │
└───────┼─────────────┼─────────────┼───────────────────────────-──┘
        └─────────────┴─────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CV Detection Pipeline                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  YOLOv8 Detection  →  Severity Classifier  →  Geotagger │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────┘
                               │ Pothole Records (PostgreSQL)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                                  │
│  ┌────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │ /api/detect│  │ /api/potholes│  │ /api/complaints         │  │
│  │ /api/       │  │ (CRUD +      │  │ (file, track, escalate) │  │
│  │  analytics │  │  heatmap)    │  │                         │  │
│  └────────────┘  └──────────────┘  └─────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
    ┌──────────────┐  ┌────────────────┐  ┌─────────────────┐
    │  PostgreSQL  │  │     Redis      │  │  Gov. Portals   │
    │  (records)   │  │  (cache/queue) │  │  (mock/real)    │
    └──────────────┘  └────────────────┘  └─────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Resolution Tracking                             │
│  Celery Tasks: poll portal → re-scan → escalate → verify        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   React Frontend                                   │
│  Dashboard | Map View | Pothole List | Complaints | Analytics    │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Backend (`backend/`)

```
app/
├── main.py              # FastAPI app factory, CORS, lifespan
├── config.py            # Pydantic settings (env vars)
├── database.py          # SQLAlchemy engine, Base, session
├── api/
│   ├── detection.py     # POST /api/detect — upload & detect
│   ├── monitoring.py    # GET /api/potholes — list, detail, heatmap
│   ├── complaints.py    # POST/GET /api/complaints — file & track
│   └── analytics.py     # GET /api/analytics — dashboard metrics
├── models/
│   ├── pothole.py       # Pothole ORM model + enums
│   ├── complaint.py     # Complaint ORM model
│   └── resolution.py    # Resolution ORM model
├── services/
│   ├── cv_pipeline.py   # YOLOv8 detection wrapper + mock fallback
│   ├── severity_classifier.py  # Severity from pixel dimensions
│   ├── complaint_filer.py      # Auto-file complaints to portals
│   ├── resolution_tracker.py   # Escalation & verification logic
│   └── risk_analyzer.py        # Risk scoring & priority queue
└── utils/
    ├── geolocation.py   # Reverse geocoding, km marker
    ├── image_processor.py  # Resize, EXIF GPS, thumbnails
    └── portal_api.py    # Mock portal API client
```

### Frontend (`frontend/src/`)

```
components/
├── Dashboard/           # KPI cards, summary stats, charts
├── MapView/             # Leaflet map with pothole markers + heatmap
├── PotholeList/         # Sortable/filterable pothole table
├── Analytics/           # Area/bar/pie charts + trend data
└── ComplaintTracker/    # Complaint status table + escalation trigger
services/
└── api.ts               # Axios wrappers for all API calls
types/
└── index.ts             # TypeScript interfaces (Pothole, Complaint, etc.)
```

## Data Flow

### Detection Pipeline

1. Image uploaded via `POST /api/detect/`
2. Image validated and resized
3. GPS coordinates extracted from EXIF or form input
4. YOLOv8 runs inference → bounding boxes
5. For each detection:
   - `SeverityClassifier` computes depth/dimensions
   - `GeoLocator` reverse-geocodes coordinates
   - `RiskAnalyzer` computes risk score
   - `Pothole` record saved to PostgreSQL
6. Response returned with detected potholes

### Complaint Filing Pipeline

1. `POST /api/complaints/` with `pothole_id`
2. `ComplaintFiler.file_complaint()` builds form data
3. Portal selected based on state/type
4. Mock submission → tracking ID generated
5. `Complaint` record saved
6. `Pothole.status` updated to `complaint_filed`

### Escalation Pipeline

1. Celery beat (or manual trigger) calls `POST /api/complaints/escalate-all`
2. `ResolutionTracker.check_and_escalate()` loops all open complaints
3. Based on `days_since_filing`:
   - Day 7: Level 1 escalation
   - Day 14: Level 2 (higher authority)
   - Day 30: Publicly flagged on dashboard
4. Portal notified (mock)

### Resolution Verification

1. `POST /api/complaints/{id}/verify` with verification image URL
2. Before/after image comparison (mock: SSIM)
3. If pothole no longer present → mark `resolved` + `verified`
4. If still present → note added, re-escalation scheduled

## Database Schema

```sql
potholes (
  id, latitude, longitude, severity, status,
  length_cm, width_cm, depth_cm, area_sqm,
  road_name, highway_name, km_marker, address, state, district,
  image_url, thumbnail_url, source_type,
  confidence_score, detection_model, risk_score, priority_rank,
  detected_at, updated_at
)

complaints (
  id, pothole_id FK, portal, complaint_id, status,
  form_data JSON, portal_response JSON,
  filed_at, last_checked, resolved_at,
  escalation_level, escalated_at, notes,
  created_at, updated_at
)

resolutions (
  id, complaint_id FK,
  resolved_at, verified_at, verification_image_url,
  before_image_url, after_image_url,
  similarity_score, repair_quality,
  is_verified, verification_notes, verified_by,
  rescan_latitude, rescan_longitude,
  pothole_still_present, pothole_depth_after,
  created_at, updated_at
)
```
