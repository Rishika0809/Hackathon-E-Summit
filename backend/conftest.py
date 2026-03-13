"""
pytest configuration — override database URL to SQLite for all tests.
Must run before any app imports.
"""
import os

# Use SQLite for all tests (no PostgreSQL required)
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_pothole.db")
