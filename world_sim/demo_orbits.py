"""Steps 1 and 2: fly the constellation for one orbit and print where it is.

Run from the repo root:
    python -m world_sim.demo_orbits
"""

from itertools import combinations

from skyfield.api import wgs84

from world_sim.constellation import (
    CONSTELLATION,
    EPOCH,
    build_constellation,
    period_minutes,
    ts,
)
from world_sim.geometry import grazing_altitude_km, has_line_of_sight

STEP_MIN = 5


def main() -> None:
    sats = build_constellation()
    period = period_minutes(CONSTELLATION[0].altitude_km)
    print(f"Orbital period at {CONSTELLATION[0].altitude_km:.0f} km: {period:.1f} min\n")

    # One time array covering one orbit; Skyfield computes all steps at once.
    minutes = range(0, int(period) + 1, STEP_MIN)
    times = ts.utc(*EPOCH.utc[:4], [EPOCH.utc[4] + m for m in minutes])

    # Where each satellite is, as seen from Earth (latitude, longitude, altitude).
    header = "T+min " + "".join(f"| {name:^24} " for name in sats)
    print(header)
    print("      " + "| lat     lon      alt km  " * len(sats))
    positions = {name: sat.at(times) for name, sat in sats.items()}
    for i, m in enumerate(minutes):
        row = f"{m:5d} "
        for name in sats:
            geo = positions[name][i]
            lat = wgs84.latlon_of(geo)[0].degrees
            lon = wgs84.latlon_of(geo)[1].degrees
            alt = wgs84.height_of(geo).km
            row += f"| {lat:6.1f} {lon:7.1f} {alt:7.0f}  "
        print(row)

    # Can neighbors see each other? Check every pair at every step.
    print("\nLaser line of sight (worst case over the orbit):")
    for a, b in combinations(sats, 2):
        lows = [
            grazing_altitude_km(positions[a][i].position.km, positions[b][i].position.km)
            for i in range(len(minutes))
        ]
        always = all(
            has_line_of_sight(positions[a][i].position.km, positions[b][i].position.km)
            for i in range(len(minutes))
        )
        status = "always visible" if always else "BLOCKED by Earth"
        print(f"  {a:7} <-> {b:7}: lowest beam altitude {min(lows):7.0f} km -> {status}")


if __name__ == "__main__":
    main()
