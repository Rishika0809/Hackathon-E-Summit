"""
Seed the database with sample pothole, complaint, and resolution data.
Useful for demo and development.
"""
import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database import SessionLocal, engine, Base
from app.models.pothole import Pothole, SeverityLevel, PotholeStatus
from app.models.complaint import Complaint, ComplaintStatus, PortalType
from app.models.resolution import Resolution

# India highway corridors for seed data
HIGHWAYS = [
    {"name": "NH-44", "state": "Maharashtra", "district": "Nagpur", "lat_range": (20.0, 21.5), "lon_range": (78.5, 79.5)},
    {"name": "NH-48", "state": "Karnataka", "district": "Bengaluru Rural", "lat_range": (12.5, 14.0), "lon_range": (77.0, 78.0)},
    {"name": "NH-19", "state": "Uttar Pradesh", "district": "Varanasi", "lat_range": (25.0, 26.0), "lon_range": (82.0, 83.5)},
    {"name": "NH-27", "state": "Rajasthan", "district": "Jaipur", "lat_range": (26.5, 27.5), "lon_range": (75.5, 77.0)},
    {"name": "NH-16", "state": "Andhra Pradesh", "district": "Visakhapatnam", "lat_range": (17.0, 18.5), "lon_range": (82.0, 83.5)},
]


def seed(n_potholes: int = 30):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(Pothole).count()
        if existing > 0:
            print(f"Database already has {existing} potholes. Skipping seed.")
            return

        print(f"Seeding {n_potholes} potholes...")
        severities = [SeverityLevel.MINOR, SeverityLevel.MODERATE, SeverityLevel.SEVERE]
        severity_weights = [0.4, 0.4, 0.2]

        potholes = []
        for i in range(n_potholes):
            hw = random.choice(HIGHWAYS)
            lat = random.uniform(*hw["lat_range"])
            lon = random.uniform(*hw["lon_range"])
            sev = random.choices(severities, weights=severity_weights)[0]
            depth = {"minor": random.uniform(1, 5), "moderate": random.uniform(5, 15), "severe": random.uniform(15, 40)}[sev.value]

            p = Pothole(
                latitude=round(lat, 5),
                longitude=round(lon, 5),
                severity=sev,
                status=random.choice(list(PotholeStatus)),
                length_cm=round(random.uniform(10, 80), 1),
                width_cm=round(random.uniform(8, 60), 1),
                depth_cm=round(depth, 1),
                area_sqm=round(random.uniform(0.01, 0.5), 3),
                road_name=hw["name"],
                highway_name=hw["name"],
                km_marker=f"KM {random.randint(10, 500)}",
                address=f"Near {hw['name']}, {hw['district']}, {hw['state']}",
                state=hw["state"],
                district=hw["district"],
                source_type=random.choice(["satellite", "drone", "dashcam"]),
                confidence_score=round(random.uniform(0.6, 0.98), 3),
                detection_model="YOLOv8",
                risk_score=round(random.uniform(20, 95), 1),
                detected_at=datetime.utcnow() - timedelta(days=random.randint(0, 60)),
            )
            db.add(p)
            potholes.append(p)

        db.flush()

        # Add complaints for ~70% of potholes
        complaints = []
        for p in potholes:
            if random.random() < 0.7:
                import uuid
                days_ago = random.randint(1, 30)
                c = Complaint(
                    pothole_id=p.id,
                    portal=random.choice(list(PortalType)),
                    complaint_id=f"MOCK-{uuid.uuid4().hex[:10].upper()}",
                    status=random.choice(list(ComplaintStatus)),
                    filed_at=datetime.utcnow() - timedelta(days=days_ago),
                    last_checked=datetime.utcnow() - timedelta(hours=random.randint(1, 24)),
                    escalation_level=random.choices([0, 1, 2], weights=[0.7, 0.2, 0.1])[0],
                    form_data={"pothole_id": p.id, "severity": p.severity.value},
                    portal_response={"success": True, "tracking_id": f"TK-{uuid.uuid4().hex[:8].upper()}"},
                )
                db.add(c)
                complaints.append(c)
                p.status = PotholeStatus.COMPLAINT_FILED

        db.flush()

        # Add resolutions for ~30% of complaints
        for c in complaints:
            if random.random() < 0.3:
                r = Resolution(
                    complaint_id=c.id,
                    resolved_at=datetime.utcnow() - timedelta(days=random.randint(1, 15)),
                    verified_at=datetime.utcnow() - timedelta(days=random.randint(0, 5)),
                    similarity_score=round(random.uniform(0.80, 0.99), 3),
                    repair_quality=random.choice(["good", "partial"]),
                    is_verified=True,
                    verified_by="system",
                    pothole_still_present=False,
                )
                db.add(r)
                c.status = ComplaintStatus.RESOLVED
                c.resolved_at = r.resolved_at

        db.commit()
        print(f"Seeded: {len(potholes)} potholes, {len(complaints)} complaints")
        print("Done!")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
