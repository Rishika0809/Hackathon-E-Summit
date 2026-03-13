# Autonomous Pothole Intelligence System — Chhattisgarh Roads

## PS 02: Road Safety - AI + Remote Sensing

An end-to-end autonomous system that detects potholes on **Chhattisgarh state highways**, classifies them by severity, automatically files complaints through government grievance portals, and tracks resolution to closure.

## Problem Statement

Build a system that autonomously detects potholes on highway stretches in **Chhattisgarh**, geolocates and classifies them by severity, and initiates a complaint through the appropriate government grievance channel with no human needed to trigger it.

The system must process road surface data at scale and produce actionable and trackable grievance records that do not get lost in a queue.

## Geographic Scope

This system is specifically configured for **Chhattisgarh** roads and highways:

| Highway | Corridor | District |
|---------|----------|----------|
| NH-130 | Raipur–Naya Raipur–Dhamtari | Raipur |
| NH-30 | Raipur–Bilaspur–Ambikapur | Bilaspur |
| NH-43 | Raipur–Durg–Rajnandgaon | Durg |
| NH-53 | Bilaspur–Raigarh–Jharsuguda | Raigarh |
| NH-63 | Jagdalpur–Vizag (Bastar) | Bastar |
| NH-130A | Bilaspur–Korba–Katghora | Korba |

## Dataset

The system uses **YOLOv8** for pothole detection. The following datasets are recommended for training and evaluation on Chhattisgarh roads:

| Dataset | Description | Usage |
|---------|-------------|-------|
| **[RDD2022](https://github.com/sekilab/RoaddamageDetector)** | Road Damage Detection challenge dataset with annotated Indian road images | Primary training dataset; includes D00 (longitudinal cracks), D10 (transverse cracks), D20 (alligator cracks), D40 (potholes) |
| **[Kaggle Pothole Detection](https://www.kaggle.com/datasets/sachinpatel21/pothole-image-dataset)** | 600+ annotated pothole images in YOLO format | Supplementary pothole-specific training |
| **Custom Chhattisgarh Collection** | Dashcam/drone imagery collected from NH-130, NH-30, NH-43, NH-53 corridors | Fine-tuning for Chhattisgarh road conditions (laterite soil, monsoon damage patterns) |

### Preparing the Dataset

1. Download the base dataset (RDD2022 India subset or Kaggle pothole dataset)
2. Convert to YOLO format with a `data.yaml`:
   ```yaml
   path: /path/to/chhattisgarh_pothole_dataset
   train: images/train
   val: images/val
   nc: 1
   names: ['pothole']
   ```
3. (Optional) Augment with Chhattisgarh-specific dashcam/drone imagery for better local accuracy
4. Train: `python backend/ml/train.py --data /path/to/data.yaml --epochs 100`

> **Note:** The system includes a mock detection fallback that works without a trained model, generating realistic pothole data for Chhattisgarh highway locations during development and demos.

## Key Features

- **Computer Vision Detection**: YOLOv8-based pothole detection with mock fallback for satellite/drone/dashcam imagery
- **Severity Classification**: Automatic minor/moderate/severe scoring based on detected dimensions
- **Precise Geotagging**: GPS extraction from EXIF data + reverse geocoding to road/highway details
- **Automated Complaint Filing**: Mock Chhattisgarh state portal / PG Portal integration with tracking ID generation
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