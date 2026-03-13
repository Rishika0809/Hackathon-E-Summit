#!/usr/bin/env bash
# run_pipeline.sh — Start the complete Pothole Intelligence pipeline
set -e

echo "===================================="
echo "  Autonomous Pothole Intelligence"
echo "  System Pipeline Runner"
echo "===================================="

# Check Python
if ! command -v python &> /dev/null; then
  echo "Python not found. Please install Python 3.11+"
  exit 1
fi

# Navigate to backend
cd "$(dirname "$0")/../backend"

# Install dependencies if needed
if [ ! -d ".venv" ]; then
  echo "[1/4] Creating virtual environment..."
  python -m venv .venv
fi

echo "[1/4] Activating virtual environment..."
source .venv/bin/activate || source .venv/Scripts/activate 2>/dev/null || true

echo "[2/4] Installing Python dependencies..."
pip install -r requirements.txt --quiet

echo "[3/4] Setting up database..."
python -c "
from app.database import engine, Base
import app.models
Base.metadata.create_all(bind=engine)
print('Database tables created.')
"

echo "[4/4] Starting FastAPI server..."
echo "API available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
