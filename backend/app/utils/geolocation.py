"""
Geolocation utilities for pothole geotagging and road identification.
"""
import logging
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False
    logger.warning("geopy not available; using mock geocoding.")


@dataclass
class GeoInfo:
    latitude: float
    longitude: float
    address: Optional[str] = None
    road_name: Optional[str] = None
    highway_name: Optional[str] = None
    km_marker: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    country: Optional[str] = "India"


class GeoLocator:
    """
    Extracts address and road information from GPS coordinates.
    """

    def __init__(self):
        if GEOPY_AVAILABLE:
            self.geocoder = Nominatim(user_agent="pothole-ai-system", timeout=5)
        else:
            self.geocoder = None

    def reverse_geocode(self, latitude: float, longitude: float) -> GeoInfo:
        """Reverse geocode a coordinate pair to address components."""
        geo = GeoInfo(latitude=latitude, longitude=longitude)

        if self.geocoder:
            try:
                location = self.geocoder.reverse(f"{latitude}, {longitude}", language="en")
                if location and location.raw:
                    geo = self._parse_nominatim(latitude, longitude, location.raw)
            except (GeocoderTimedOut, GeocoderUnavailable) as e:
                logger.warning(f"Geocoding failed: {e}")
            except Exception as e:
                logger.error(f"Unexpected geocoding error: {e}")
        else:
            geo = self._mock_geocode(latitude, longitude)

        return geo

    def _parse_nominatim(self, lat: float, lon: float, raw: dict) -> GeoInfo:
        addr = raw.get("address", {})
        road = addr.get("road") or addr.get("highway") or addr.get("motorway") or addr.get("trunk")
        state = addr.get("state")
        district = addr.get("county") or addr.get("district") or addr.get("city")

        # Detect highway name from road
        highway_name = None
        if road:
            import re
            nh_match = re.search(r"(NH|SH|MDR)\s*[-–]?\s*(\d+[A-Za-z]?)", road, re.IGNORECASE)
            if nh_match:
                highway_name = nh_match.group(0).upper()

        return GeoInfo(
            latitude=lat,
            longitude=lon,
            address=raw.get("display_name", ""),
            road_name=road,
            highway_name=highway_name,
            state=state,
            district=district,
        )

    def _mock_geocode(self, lat: float, lon: float) -> GeoInfo:
        """Mock geocoding for testing without network access."""
        return GeoInfo(
            latitude=lat,
            longitude=lon,
            address=f"Near NH-130, Raipur–Bilaspur Highway, Chhattisgarh (approx. Lat:{lat:.4f}, Lon:{lon:.4f})",
            road_name="NH-130",
            highway_name="NH-130",
            km_marker=f"KM {int(abs(lat * 10) % 500)}",
            state="Chhattisgarh",
            district="Raipur",
        )

    def estimate_km_marker(self, lat: float, lon: float, highway_start_lat: float, highway_start_lon: float) -> str:
        """Estimate km marker from highway start point using Haversine distance."""
        km = self._haversine_km(lat, lon, highway_start_lat, highway_start_lon)
        return f"KM {km:.1f}"

    @staticmethod
    def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        import math
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


_locator: Optional[GeoLocator] = None


def get_geo_locator() -> GeoLocator:
    global _locator
    if _locator is None:
        _locator = GeoLocator()
    return _locator
