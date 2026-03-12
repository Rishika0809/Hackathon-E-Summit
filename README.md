# Autonomous Pothole Intelligence System

## PS 02: Road Safety - AI + Remote Sensing

An end-to-end autonomous system that detects potholes on highways, classifies them by severity, automatically files complaints through government grievance portals, and tracks resolution to closure.

## Problem Statement

Build a system that autonomously detects potholes on highway stretches, geolocates and classifies them by severity, and initiates a complaint through the appropriate government grievance channel with no human needed to trigger it.

The system must process road surface data at scale and produce actionable and trackable grievance records that do not get lost in a queue.

## Key Features

- **Computer Vision Detection**: Pothole detection using YOLOv8 on satellite/drone imagery
- **Severity Classification**: Automated severity scoring and precise geotagging
- **Automated Complaint Filing**: API-based integration with PG Portal and state grievance systems
- **Resolution Tracking**: Re-detection to verify repairs and intelligent re-escalation
- **Risk Assessment**: Priority heat maps based on accident risk
- **Monitoring Dashboard**: Complete lifecycle tracking from detection to resolution

## Tech Stack

- **Backend**: Python (FastAPI), PyTorch, YOLOv8, OpenCV
- **Frontend**: React.js, TypeScript, Leaflet.js
- **Database**: PostgreSQL, Redis
- **ML**: Computer Vision, Object Detection, Severity Classification
- **APIs**: Government portal integration, Maps API

## Project Status

🚧 Under Development for E-Summit Hackathon

## License

MIT