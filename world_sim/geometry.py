"""Geometry helpers: line of sight between two satellites."""

import numpy as np

from world_sim.constellation import R_EARTH_KM

# A laser beam that skims too close to Earth passes through atmosphere.
# Require the line between two satellites to stay at least this high.
MIN_GRAZING_ALTITUDE_KM = 100.0


def grazing_altitude_km(p1_km: np.ndarray, p2_km: np.ndarray) -> float:
    """Lowest altitude of the straight line between two positions.

    Positions are vectors from Earth's center, in km. We find the point on
    the segment p1 -> p2 closest to Earth's center and return its altitude.
    """
    d = p2_km - p1_km
    # Parameter t in [0, 1] of the closest point on the segment.
    t = np.clip(-np.dot(p1_km, d) / np.dot(d, d), 0.0, 1.0)
    closest = p1_km + t * d
    return float(np.linalg.norm(closest) - R_EARTH_KM)


def has_line_of_sight(p1_km: np.ndarray, p2_km: np.ndarray) -> bool:
    return grazing_altitude_km(p1_km, p2_km) >= MIN_GRAZING_ALTITUDE_KM
