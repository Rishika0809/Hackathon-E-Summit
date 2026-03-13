# API Documentation

## Base URL

```
http://localhost:8000
```

Interactive API docs: `http://localhost:8000/docs`

---

## Authentication

Currently no authentication required (development mode). Production deployment should add JWT or API key auth.

---

## Endpoints

### Health

#### `GET /`
Returns service info.

**Response:**
```json
{
  "service": "Autonomous Pothole Intelligence System",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

#### `GET /health`
Health check.

---

### Detection

#### `POST /api/detect/`
Upload a road image for pothole detection.

**Request:** `multipart/form-data`
- `file` (required): Image file (JPEG/PNG, max 10 MB)
- `latitude` (optional): GPS latitude
- `longitude` (optional): GPS longitude
- `source_type` (optional): `satellite` | `drone` | `dashcam` (default: `dashcam`)

**Response:**
```json
{
  "detected": true,
  "count": 2,
  "potholes": [
    {
      "id": 1,
      "latitude": 21.2514,
      "longitude": 81.6296,
      "severity": "moderate",
      "status": "classified",
      "depth_cm": 8.5,
      "risk_score": 62.3,
      "detected_at": "2024-01-15T10:30:00"
    }
  ],
  "image_path": "uploads/detect_abc123.jpg"
}
```

#### `POST /api/detect/batch`
Batch process multiple images.

**Request:** `multipart/form-data`
- `files[]`: Multiple image files
- `source_type`: Source type

---

### Potholes

#### `GET /api/potholes/`
List all detected potholes with optional filters.

**Query Parameters:**
- `severity`: `minor` | `moderate` | `severe`
- `status`: `detected` | `classified` | `complaint_filed` | `in_progress` | `resolved` | `verified` | `escalated`
- `state`: State name filter (default scope: Chhattisgarh)
- `min_risk`: Minimum risk score
- `skip`: Pagination offset (default: 0)
- `limit`: Results per page (default: 100)

**Response:**
```json
{
  "total": 45,
  "skip": 0,
  "limit": 100,
  "potholes": [...]
}
```

#### `GET /api/potholes/{id}`
Get pothole details including complaints.

#### `GET /api/potholes/heatmap/data`
Get risk heat map data points for frontend visualization.

**Response:**
```json
{
  "points": [
    { "lat": 21.2514, "lon": 81.6296, "intensity": 0.75, "severity": "severe", "pothole_id": 1 }
  ],
  "total": 45
}
```

#### `GET /api/potholes/priority/queue`
Get potholes sorted by risk score (highest priority first), filtered to unprocessed potholes.

---

### Complaints

#### `POST /api/complaints/`
File a complaint for a pothole.

**Request Body:**
```json
{
  "pothole_id": 1,
  "notes": "Optional notes"
}
```

**Response:** Complaint object with portal tracking ID.

#### `GET /api/complaints/`
List complaints with optional status filter.

**Query Parameters:**
- `status`: ComplaintStatus filter
- `pothole_id`: Filter by pothole ID
- `skip`, `limit`: Pagination

#### `GET /api/complaints/{id}`
Get complaint details.

#### `POST /api/complaints/{id}/verify`
Verify that a pothole has been repaired.

**Query Parameters:**
- `verification_image_url`: URL of verification image (optional)

#### `POST /api/complaints/escalate-all`
Run escalation check on all open complaints.

**Response:**
```json
{
  "message": "Escalation sweep complete",
  "summary": {
    "checked": 12,
    "escalated_l1": 2,
    "escalated_l2": 1,
    "flagged": 0,
    "closed": 0
  }
}
```

---

### Analytics

#### `GET /api/analytics/`
Get dashboard analytics.

**Response:**
```json
{
  "summary": {
    "total_potholes": 45,
    "total_complaints": 32,
    "total_resolved": 18,
    "resolution_rate": 56.2,
    "avg_risk_score": 54.3
  },
  "severity_breakdown": [
    { "name": "Minor", "value": 15 },
    { "name": "Moderate", "value": 22 },
    { "name": "Severe", "value": 8 }
  ],
  "status_breakdown": [...],
  "complaint_breakdown": [...]
}
```

#### `GET /api/analytics/kpis`
Get KPI metrics for the monitoring dashboard.

---

## Data Models

### Pothole

| Field | Type | Description |
|-------|------|-------------|
| id | int | Unique ID |
| latitude | float | GPS latitude |
| longitude | float | GPS longitude |
| severity | enum | minor/moderate/severe |
| status | enum | Pipeline status |
| depth_cm | float | Estimated depth |
| risk_score | float | 0–100 risk score |
| detected_at | datetime | Detection timestamp |

### Complaint

| Field | Type | Description |
|-------|------|-------------|
| id | int | Unique ID |
| pothole_id | int | Foreign key |
| complaint_id | string | Portal tracking ID |
| portal | enum | pg_portal/state_portal/municipal/mock |
| status | enum | Complaint lifecycle status |
| escalation_level | int | 0=none, 1=first, 2=higher authority |

### Resolution

| Field | Type | Description |
|-------|------|-------------|
| id | int | Unique ID |
| complaint_id | int | Foreign key |
| is_verified | bool | Repair verified |
| similarity_score | float | Before/after image similarity |
| repair_quality | string | good/partial/poor |

---

## Escalation Logic

| Days Since Filing | Action |
|-------------------|--------|
| 7 days | First escalation (escalation_level = 1) |
| 14 days | Higher authority escalation (escalation_level = 2) |
| 30 days | Publicly flagged on dashboard |
