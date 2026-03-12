# Autonomous Pothole Intelligence System

## PS 02: Road Safety - AI + Remote Sensing

An end-to-end autonomous system that detects potholes on highways, classifies them by severity, automatically files complaints through government grievance portals, and tracks resolution to closure.

## Problem Statement

Build a system that autonomously detects potholes on highway stretches, geolocates and classifies them by severity, and initiates a complaint through the appropriate government grievance channel with no human needed to trigger it.

The system must process road surface data at scale and produce actionable and trackable grievance records that do not get lost in a queue.

## Key Features

- **Computer Vision Detection**: YOLOv8-based pothole detection with mock fallback for satellite/drone/dashcam imagery
- **Severity Classification**: Automatic minor/moderate/severe scoring based on detected dimensions
- **Precise Geotagging**: GPS extraction from EXIF data + reverse geocoding to road/highway details
- **Automated Complaint Filing**: Mock PG Portal / state portal integration with tracking ID generation
- **Resolution Tracking**: Re-scan verification, before/after comparison, and intelligent re-escalation
- **Risk Assessment**: Accident risk scoring (severity + traffic + speed + weather + location)
- **Priority Queue**: Complaints filed in order of risk score
- **Interactive Dashboard**: React frontend with map, charts, complaint tracker, and analytics

## Project Structure

```
/
├── backend/              # FastAPI Python backend
│   ├── app/
│   │   ├── api/          # Route handlers (detection, complaints, monitoring, analytics)
│   │   ├── models/       # SQLAlchemy ORM models (Pothole, Complaint, Resolution)
│   │   ├── services/     # Business logic (CV pipeline, classifier, filer, tracker, risk)
│   │   └── utils/        # Geolocation, image processing, portal API client
│   ├── ml/               # YOLOv8 train/inference/download scripts
│   ├── tests/            # pytest test suite
│   └── requirements.txt
├── frontend/             # React TypeScript dashboard
│   └── src/
│       ├── components/   # Dashboard, MapView, PotholeList, Analytics, ComplaintTracker
│       ├── services/     # API client (axios)
│       └── types/        # TypeScript interfaces
├── docker/               # Dockerfiles + docker-compose.yml
├── scripts/              # DB setup, seed data, pipeline runner
├── docs/                 # API.md, ARCHITECTURE.md, DEPLOYMENT.md
├── .env.example
└── .gitignore
```

## Quick Start

### Docker (Recommended)

```bash
cp .env.example .env
cd docker
docker compose up --build -d
```

- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Local Development

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install && npm start

# Seed demo data
python scripts/seed_data.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/detect/` | Upload image for pothole detection |
| GET | `/api/potholes/` | List all detected potholes |
| GET | `/api/potholes/{id}` | Get pothole details |
| GET | `/api/potholes/heatmap/data` | Risk heat map data |
| GET | `/api/potholes/priority/queue` | Priority-sorted queue |
| POST | `/api/complaints/` | File a complaint |
| GET | `/api/complaints/{id}` | Track complaint status |
| POST | `/api/complaints/escalate-all` | Run escalation check |
| POST | `/api/complaints/{id}/verify` | Verify resolution |
| GET | `/api/analytics/` | Dashboard analytics |
| GET | `/api/analytics/kpis` | KPI metrics |

## Escalation Logic

| Threshold | Action |
|-----------|--------|
| 7 days unresolved | First escalation |
| 14 days unresolved | Higher authority escalation |
| 30 days unresolved | Public dashboard flagging |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python FastAPI |
| ML/CV | PyTorch, YOLOv8 (ultralytics), OpenCV |
| Database | PostgreSQL + SQLAlchemy |
| Cache/Queue | Redis + Celery |
| Geospatial | GeoPy, Folium |
| Frontend | React 18 + TypeScript |
| Maps | Leaflet.js + react-leaflet |
| Charts | Recharts |
| Containerization | Docker + Docker Compose |

## Documentation

- [API Reference](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## License

MIT