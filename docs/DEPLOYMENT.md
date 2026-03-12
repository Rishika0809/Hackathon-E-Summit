# Deployment Guide

## Prerequisites

- Docker 24+
- Docker Compose v2+
- 4 GB RAM minimum
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)

---

## 1. Docker Deployment (Recommended)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/Rishika0809/Hackathon-E-Summit.git
cd Hackathon-E-Summit

# Copy environment config
cp .env.example .env
# Edit .env with your settings if needed

# Start all services
cd docker
docker compose up --build -d

# Check logs
docker compose logs -f backend
```

Services will be available at:
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Seed Demo Data

```bash
docker compose exec backend python /app/../scripts/seed_data.py
```

### Stop Services

```bash
docker compose down
# Remove volumes too:
docker compose down -v
```

---

## 2. Local Development

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp ../.env.example .env
# Configure DATABASE_URL, REDIS_URL, etc.

# Setup database (requires PostgreSQL running)
python -c "from app.database import engine, Base; import app.models; Base.metadata.create_all(engine)"

# Seed demo data
python ../scripts/seed_data.py

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
# Opens http://localhost:3000
```

### Using the Pipeline Script

```bash
chmod +x scripts/run_pipeline.sh
./scripts/run_pipeline.sh
```

---

## 3. ML Model Setup

### Download Pretrained Model

```bash
cd backend
python ml/download_model.py --variant nano --output ml/models
```

### Train on Custom Dataset

1. Prepare dataset in YOLO format with `data.yaml`:
   ```yaml
   path: /path/to/dataset
   train: images/train
   val: images/val
   nc: 1
   names: ['pothole']
   ```

2. Run training:
   ```bash
   python ml/train.py --data /path/to/data.yaml --epochs 100 --batch 16
   ```

3. Update `.env`:
   ```
   MODEL_PATH=ml/runs/pothole_v1/weights/best.pt
   ```

### Run Standalone Inference

```bash
python ml/inference.py --image /path/to/image.jpg --model ml/models/yolov8n.pt --output output/
```

---

## 4. Environment Variables

See `.env.example` for all available configuration options.

Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | PostgreSQL URL | Database connection |
| `REDIS_URL` | Redis URL | Cache and task queue |
| `MODEL_PATH` | `ml/models/yolov8_pothole.pt` | YOLO model path |
| `MODEL_CONFIDENCE` | `0.5` | Detection confidence threshold |
| `UPLOAD_DIR` | `uploads` | Image upload directory |
| `FIRST_ESCALATION_DAYS` | `7` | Days before first escalation |
| `SECOND_ESCALATION_DAYS` | `14` | Days before second escalation |
| `PUBLIC_FLAG_DAYS` | `30` | Days before public flagging |

---

## 5. Running Tests

```bash
cd backend

# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/ -v

# Run specific test module
pytest tests/test_detection.py -v
pytest tests/test_api.py -v
```

---

## 6. Production Considerations

- Replace mock portal API with real PG Portal / state portal credentials
- Add authentication (JWT) to all API endpoints
- Set up SSL/TLS via nginx with Let's Encrypt
- Configure Celery beat for scheduled escalation checks
- Set up object storage (S3/MinIO) for image uploads
- Enable database connection pooling (already configured)
- Set `DEBUG=false` in production `.env`
