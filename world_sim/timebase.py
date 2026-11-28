"""The project's single time scale: GPS time.

Every part of the system (world sim, flight software, gateways, mission
control) counts time as **GPS seconds**: seconds since the GPS epoch,
1980-01-06 00:00:00. GPS time has no leap seconds, so it never jumps,
which is what onboard software needs. Packets carry it as a CCSDS CUC
timestamp (CCSDS 301.0-B) with the GPS epoch as the agency-defined epoch.

Conversions to other scales happen only at the edges:
  - UTC: only for display to humans (mission control screens, printouts).
  - TT:  only inside Skyfield, which needs it for astronomy.

Relationship: GPS = TAI - 19 s, so GPS epoch = TAI 1980-01-06 00:00:19.
UTC currently lags GPS by 18 s (leap seconds); Skyfield handles that.
"""

import numpy as np
from skyfield.api import load
from skyfield.timelib import Time

ts = load.timescale()

GPS_MINUS_TAI_S = -19.0


def from_gps_seconds(gps_s) -> Time:
    """GPS seconds (a float or a NumPy array) -> Skyfield Time."""
    return ts.tai(1980, 1, 6, 0, 0, 19.0 + np.asarray(gps_s, dtype=float))


def to_gps_seconds(t: Time):
    """Skyfield Time -> GPS seconds."""
    tai_days_since_gps_epoch = t.tai - ts.tai(1980, 1, 6, 0, 0, 19.0).tai
    return tai_days_since_gps_epoch * 86400.0


def utc_label(t: Time) -> str:
    """For human display only."""
    return t.utc_strftime("%Y-%m-%d %H:%M:%S UTC")
