"""Orbit definitions for the three-satellite constellation.

The world sim is "the universe": it holds the TRUE position of every
satellite. Flight software and mission control never import this module;
they only learn positions through telemetry (see docs/conops.md, section 4).

How a satellite is defined here
-------------------------------
Real satellites are usually loaded from a TLE (two-line element set)
published by tracking agencies. Ours don't exist, so we build them from
orbital elements instead and feed those to SGP4, the same propagator that
TLEs are designed for.

A circular orbit needs only four numbers:
  - altitude      -> sets the semi-major axis a = R_earth + altitude,
                     and from that the mean motion n = sqrt(mu / a^3)
  - inclination   -> tilt of the orbital plane from the equator
  - RAAN          -> "right ascension of the ascending node": which way the
                     plane is rotated around Earth's axis. Same RAAN means
                     same plane.
  - mean anomaly  -> where along the orbit the satellite starts. Spacing
                     the satellites 40 degrees apart in mean anomaly puts
                     them one behind another in the same plane.
"""

from dataclasses import dataclass
from math import pi, radians, sqrt

from sgp4.api import WGS72, Satrec
from skyfield.api import EarthSatellite

from world_sim.timebase import from_gps_seconds, to_gps_seconds, ts

MU_EARTH_KM3_S2 = 398600.4418  # Earth's gravitational parameter
R_EARTH_KM = 6378.137          # Earth's equatorial radius (WGS84)

# The moment our orbit definitions are "true". SGP4 propagates forward
# (and backward) from here. Defined in GPS time like everything else; it is
# 2027-01-01 00:00:00 UTC, rounded to a whole GPS second.
EPOCH_GPS_S = round(to_gps_seconds(ts.utc(2027, 1, 1)))
EPOCH = from_gps_seconds(EPOCH_GPS_S)


@dataclass(frozen=True)
class OrbitSpec:
    name: str
    satnum: int              # catalog number; any unique integer works
    altitude_km: float
    inclination_deg: float
    raan_deg: float
    mean_anomaly_deg: float


# Three satellites in ONE plane (same inclination and RAAN), 40 degrees
# apart along the orbit. 40 degrees is inside the ~46 degree limit where
# Earth starts blocking the line of sight between neighbors at 550 km.
# Hero and lite-2 are 80 degrees apart, so they can't see each other:
# the laser links form a chain, hero <-> lite-1 <-> lite-2.
CONSTELLATION = [
    OrbitSpec("hero",   90001, 550.0, 53.0, 0.0, 0.0),
    OrbitSpec("lite-1", 90002, 550.0, 53.0, 0.0, 40.0),
    OrbitSpec("lite-2", 90003, 550.0, 53.0, 0.0, 80.0),
]


def mean_motion_rad_per_min(altitude_km: float) -> float:
    """Kepler's third law for a circular orbit, in the units SGP4 expects."""
    a = R_EARTH_KM + altitude_km
    n_rad_per_s = sqrt(MU_EARTH_KM3_S2 / a**3)
    return n_rad_per_s * 60.0


def period_minutes(altitude_km: float) -> float:
    return 2 * pi / mean_motion_rad_per_min(altitude_km)


def build_satellite(spec: OrbitSpec) -> EarthSatellite:
    """Turn an OrbitSpec into a Skyfield satellite object."""
    sat = Satrec()
    sat.sgp4init(
        WGS72,                      # gravity model SGP4 was designed with
        "i",                        # "improved" mode (the modern default)
        spec.satnum,
        EPOCH.tt - 2433281.5,       # SGP4 counts days from 1949-12-31 00:00
        0.0,                        # bstar: drag term. 0 = no drag for now
        0.0,                        # ndot (unused by SGP4)
        0.0,                        # nddot (unused by SGP4)
        0.0,                        # eccentricity: 0 = circular
        0.0,                        # argument of perigee: meaningless when circular
        radians(spec.inclination_deg),
        radians(spec.mean_anomaly_deg),
        mean_motion_rad_per_min(spec.altitude_km),
        radians(spec.raan_deg),
    )
    return EarthSatellite.from_satrec(sat, ts)


def build_constellation() -> dict[str, EarthSatellite]:
    return {spec.name: build_satellite(spec) for spec in CONSTELLATION}
