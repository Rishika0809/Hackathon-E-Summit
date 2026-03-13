"""
Risk Assessment and Prioritization Service.
Scores potholes by accident risk and generates heat map data.
"""
import logging
import math
from dataclasses import dataclass
from typing import Optional, List

from app.models.pothole import SeverityLevel

logger = logging.getLogger(__name__)


@dataclass
class RiskScore:
    total_score: float          # 0–100
    severity_score: float
    traffic_score: float
    speed_score: float
    weather_score: float
    location_score: float       # curves/intersections
    historical_score: float
    priority_level: str         # critical, high, medium, low
    factors: List[str]


class RiskAnalyzer:
    """
    Computes accident risk score for a pothole detection.
    Higher score = higher priority for complaint filing.
    """

    # Weights
    WEIGHTS = {
        "severity": 0.30,
        "traffic": 0.20,
        "speed": 0.15,
        "weather": 0.15,
        "location": 0.10,
        "historical": 0.10,
    }

    SEVERITY_SCORES = {
        SeverityLevel.MINOR: 20,
        SeverityLevel.MODERATE: 55,
        SeverityLevel.SEVERE: 90,
    }

    def compute_risk(
        self,
        severity: SeverityLevel,
        traffic_volume: Optional[float] = None,      # vehicles/hour
        speed_limit_kmh: Optional[float] = None,
        weather_condition: Optional[str] = None,
        near_curve: bool = False,
        near_intersection: bool = False,
        historical_accidents: Optional[int] = None,
    ) -> RiskScore:
        factors = []

        # Severity score
        sev_score = self.SEVERITY_SCORES.get(severity, 55)
        if severity == SeverityLevel.SEVERE:
            factors.append("Severe pothole depth")

        # Traffic score (0–100 normalized)
        if traffic_volume is not None:
            traffic_score = min(100, (traffic_volume / 5000) * 100)
        else:
            traffic_score = 50  # assume moderate traffic
        if traffic_score > 70:
            factors.append("High traffic volume")

        # Speed score
        if speed_limit_kmh is not None:
            speed_score = min(100, (speed_limit_kmh / 120) * 100)
        else:
            speed_score = 50
        if speed_score > 75:
            factors.append("High speed limit")

        # Weather score
        weather_map = {
            "clear": 10,
            "cloudy": 20,
            "rain": 70,
            "heavy_rain": 90,
            "fog": 80,
            "ice": 95,
            "snow": 85,
        }
        if weather_condition:
            weather_score = weather_map.get(weather_condition.lower(), 30)
        else:
            weather_score = 30
        if weather_score > 60:
            factors.append(f"Adverse weather: {weather_condition}")

        # Location score
        location_score = 0
        if near_curve:
            location_score += 50
            factors.append("Near road curve")
        if near_intersection:
            location_score += 50
            factors.append("Near intersection")
        location_score = min(100, location_score)

        # Historical accidents score
        if historical_accidents is not None:
            historical_score = min(100, historical_accidents * 20)
        else:
            historical_score = 10
        if historical_score > 40:
            factors.append(f"Historical accidents: {historical_accidents}")

        # Weighted total
        total = (
            sev_score * self.WEIGHTS["severity"] +
            traffic_score * self.WEIGHTS["traffic"] +
            speed_score * self.WEIGHTS["speed"] +
            weather_score * self.WEIGHTS["weather"] +
            location_score * self.WEIGHTS["location"] +
            historical_score * self.WEIGHTS["historical"]
        )

        priority = self._score_to_priority(total)

        return RiskScore(
            total_score=round(total, 2),
            severity_score=sev_score,
            traffic_score=traffic_score,
            speed_score=speed_score,
            weather_score=weather_score,
            location_score=location_score,
            historical_score=historical_score,
            priority_level=priority,
            factors=factors,
        )

    def _score_to_priority(self, score: float) -> str:
        if score >= 75:
            return "critical"
        elif score >= 50:
            return "high"
        elif score >= 30:
            return "medium"
        else:
            return "low"

    def generate_heatmap_points(self, potholes: list) -> list:
        """
        Generate heat map data points for frontend visualization.
        Each point: [lat, lon, intensity]
        """
        points = []
        for p in potholes:
            intensity = (p.risk_score or 50) / 100.0
            points.append({
                "lat": p.latitude,
                "lon": p.longitude,
                "intensity": intensity,
                "severity": p.severity.value if p.severity else "moderate",
                "pothole_id": p.id,
            })
        return points

    def build_priority_queue(self, potholes: list) -> list:
        """Sort potholes by risk score descending for prioritized filing."""
        return sorted(
            potholes,
            key=lambda p: (p.risk_score or 0),
            reverse=True,
        )


_analyzer: Optional[RiskAnalyzer] = None


def get_risk_analyzer() -> RiskAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = RiskAnalyzer()
    return _analyzer
