"""Which gateway can see which satellite, and when."""

from dataclasses import dataclass

import numpy as np
from skyfield.api import EarthSatellite
from skyfield.timelib import Time

from world_sim.gateways import MIN_ELEVATION_DEG, Gateway


def elevation_deg(sat: EarthSatellite, gw: Gateway, times: Time) -> np.ndarray:
    """Satellite elevation above the gateway's horizon, in degrees.

    (sat - gateway) is the satellite as seen from the gateway; altaz()
    turns that into altitude above the horizon (elevation), azimuth and
    distance. Works on a whole array of times at once.
    """
    alt, _az, _dist = (sat - gw.location).at(times).altaz()
    return alt.degrees


@dataclass
class Pass:
    satellite: str
    gateway: str
    start: Time
    end: Time
    peak_elevation_deg: float
    truncated: bool = False  # cut off by the start or end of the time window

    @property
    def duration_min(self) -> float:
        return (self.end - self.start) * 24 * 60  # Time difference is in days


def find_passes(
    sat_name: str,
    sat: EarthSatellite,
    gw: Gateway,
    times: Time,
    min_elevation_deg: float = MIN_ELEVATION_DEG,
) -> list[Pass]:
    """Scan a time grid and return every stretch where the satellite is visible.

    A simple edge detector: remember whether we were visible on the previous
    step; a False -> True change starts a pass, True -> False ends it. Pass
    times are only as precise as the step size (30 s is plenty here).
    """
    elev = elevation_deg(sat, gw, times)
    visible = elev >= min_elevation_deg
    passes: list[Pass] = []
    start_i = None
    for i, vis in enumerate(visible):
        if vis and start_i is None:
            start_i = i
        elif not vis and start_i is not None:
            passes.append(Pass(sat_name, gw.name, times[start_i], times[i - 1],
                               float(elev[start_i:i].max()), truncated=start_i == 0))
            start_i = None
    if start_i is not None:  # still visible when the window ends
        passes.append(Pass(sat_name, gw.name, times[start_i], times[-1],
                           float(elev[start_i:].max()), truncated=True))
    return passes


def longest_gap_min(passes: list[Pass], window_start: Time, window_end: Time) -> float:
    """Longest stretch in the window with NO satellite visible from a gateway.

    Overlapping passes (two satellites in view at once) are merged first.
    """
    spans = sorted((p.start.tt, p.end.tt) for p in passes)
    gap = 0.0
    cursor = window_start.tt
    for start, end in spans:
        gap = max(gap, start - cursor)
        cursor = max(cursor, end)
    gap = max(gap, window_end.tt - cursor)
    return gap * 24 * 60
