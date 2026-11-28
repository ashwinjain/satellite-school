"""Step 3: list 24 hours of passes over each gateway.

Run from the repo root:
    python -m world_sim.demo_passes
"""

import numpy as np

from world_sim.constellation import EPOCH, EPOCH_GPS_S, build_constellation
from world_sim.timebase import from_gps_seconds
from world_sim.gateways import GATEWAYS, MIN_ELEVATION_DEG
from world_sim.visibility import find_passes, longest_gap_min

HOURS = 24
STEP_S = 30


def main() -> None:
    sats = build_constellation()
    # The sim clock runs in GPS seconds; Skyfield gets a converted copy.
    gps_s = EPOCH_GPS_S + np.arange(0, HOURS * 3600 + 1, STEP_S)
    times = from_gps_seconds(gps_s)

    print(f"Passes above {MIN_ELEVATION_DEG:.0f} deg elevation, {HOURS} h from "
          f"GPS second {EPOCH_GPS_S} ({EPOCH.utc_strftime('%Y-%m-%d %H:%M')} UTC)\n")

    summary = []
    for gw in GATEWAYS:
        passes = [p for name, sat in sats.items() for p in find_passes(name, sat, gw, times)]
        passes.sort(key=lambda p: p.start.tt)

        print(f"== {gw.name} ({gw.lat_deg:+.1f}, {gw.lon_deg:+.1f}) ==")
        if not passes:
            print("  no passes\n")
        for p in passes:
            print(f"  {p.satellite:7} {p.start.utc_strftime('%H:%M:%S')} - "
                  f"{p.end.utc_strftime('%H:%M:%S')}  {p.duration_min:4.1f} min  "
                  f"peak {p.peak_elevation_deg:4.1f} deg"
                  + ("  (cut off by window)" if p.truncated else ""))
        print()

        durations = [p.duration_min for p in passes if not p.truncated]
        summary.append((
            gw.name,
            len(passes),
            min(durations, default=0.0),
            max(durations, default=0.0),
            longest_gap_min(passes, times[0], times[-1]),
        ))

    print("Summary")
    print(f"  {'Gateway':11} {'passes':>6} {'shortest':>9} {'longest':>8} {'longest gap':>12}")
    for name, n, lo, hi, gap in summary:
        print(f"  {name:11} {n:6d} {lo:7.1f} m {hi:6.1f} m {gap / 60:9.1f} h")


if __name__ == "__main__":
    main()
