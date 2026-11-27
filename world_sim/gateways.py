"""Ground gateway locations.

These are PRETEND locations. Whether a gateway can see a satellite is
decided here, from geometry, not from where any server physically runs
(see docs/conops.md, section 4).
"""

from dataclasses import dataclass

from skyfield.api import wgs84
from skyfield.toposlib import GeographicPosition

# Dishes only use a satellite once it is well above the horizon: low
# elevations mean more atmosphere, more obstruction, and a longer path.
MIN_ELEVATION_DEG = 25.0


@dataclass(frozen=True)
class Gateway:
    name: str
    lat_deg: float
    lon_deg: float

    @property
    def location(self) -> GeographicPosition:
        return wgs84.latlon(self.lat_deg, self.lon_deg)


GATEWAYS = [
    Gateway("Texas", 31.0, -100.0),
    Gateway("Washington", 47.5, -120.0),
    Gateway("Frankfurt", 50.1, 8.7),
    Gateway("Sydney", -33.9, 151.2),
]
