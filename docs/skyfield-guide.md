# Skyfield Guide

What each Skyfield tool does, the code that uses it, and what it actually returned when run on our constellation (epoch 2027-01-01 00:00 UTC). Skyfield sits on top of SGP4 and handles time, coordinate frames, the Sun and the Earth's shape, so our code only has to ask questions.

Run any snippet from the repo root with `python` after `pip install -r requirements.txt`.

---

## 1. Time: `load.timescale()` and `ts.utc(...)`

Astronomy uses several clocks: UTC (with leap seconds), TT (smooth "physics" time) and others. A `Time` object holds all of them so you never convert by hand.

```python
from skyfield.api import load
ts = load.timescale()
t = ts.utc(2027, 1, 1, 0, 0, 0)
print(t.utc_strftime('%Y-%m-%d %H:%M:%S'), t.tt)

times = ts.utc(2027, 1, 1, 0, [0, 1, 2])   # a list in any field gives an ARRAY of times
print(len(times))
```

```
2027-01-01 00:00:00 2461406.500800741
3
```

- `t.tt` is the time as a Julian date (days). We use it to subtract times: `(t2 - t1) * 24 * 60` gives minutes.
- **Time arrays are the important trick.** Every later call accepts an array and computes all steps at once in NumPy, which is far faster than a Python loop. `demo_passes.py` builds 2,881 times (24 h at 30 s) in one call.
- Used in: `constellation.py` (`EPOCH`), `demo_orbits.py`, `demo_passes.py`.

## 2. Satellites: `EarthSatellite`

An object that can compute a satellite's position at any time using the SGP4 propagator. Normally built from a TLE; ours are built from orbital elements, because our satellites don't exist.

```python
from world_sim.constellation import build_constellation
hero = build_constellation()['hero']
print(hero)
```

```
catalog #90001 epoch 2027-01-01 00:00:00 UTC
```

- Inside `build_satellite()`, `Satrec.sgp4init(...)` takes the raw elements (inclination, mean anomaly, mean motion, RAAN...) and `EarthSatellite.from_satrec(...)` wraps it for Skyfield.
- SGP4 expects the epoch as a UTC date (days since 1949-12-31). An earlier version passed TT by mistake, which put the epoch at 00:01:09: TT runs 69 s ahead of UTC (37 leap seconds plus a fixed 32.184 s). `constellation.py` now converts the GPS-time epoch to UTC with `sgp4.api.jday`.

## 3. Position and velocity: `sat.at(t)`

Where the satellite is at time `t`, as a vector from Earth's center, in an inertial frame (one that doesn't rotate with Earth; called GCRS).

```python
g = hero.at(t)
print(g.position.km, g.velocity.km_per_s)
```

```
position km   [6905.4  -364.4  -446.7]   |r| = 6929.5 km
velocity km/s [0.625   4.547   6.041]    speed = 7.587 km/s
```

- |r| = 6,929.5 km is Earth's radius plus ~550 km. 7.59 km/s is orbital speed at that altitude.
- With an array of times, `position.km` becomes a 3 × N array.
- Used in: `demo_orbits.py` (positions for line of sight), `geometry.py` takes these vectors.

## 4. A place on Earth: `wgs84.latlon(lat, lon)`

A fixed point on Earth's surface on the WGS84 ellipsoid (the oblate Earth model GPS uses). Because it rotates with Earth, Skyfield always knows where it is in space.

```python
from skyfield.api import wgs84
frankfurt = wgs84.latlon(50.1, 8.7)
print(frankfurt)
```

```
WGS84 latitude +50.1000 N longitude 8.7000 E elevation 0.0 m
```

- Used in: `gateways.py` (`Gateway.location`).

## 5. Ground track: `wgs84.latlon_of()` and `wgs84.height_of()`

The point on Earth directly below the satellite, and how high above it the satellite is.

```python
lat, lon = wgs84.latlon_of(g)
print(lat.degrees, lon.degrees, wgs84.height_of(g).km)
```

```
-3.57  -103.10  551.4
```

- This is the "altitude wobble" you explained: height is measured above the ellipsoid surface directly below, which is lower near the poles.
- Used in: `demo_orbits.py` (the lat/lon/alt table). Later: ground-track plots.

## 6. View from the ground: `(sat - place).at(t).altaz()`

Subtracting a place from a satellite gives the satellite **as seen from that place**. `altaz()` turns it into the three numbers an antenna needs.

```python
alt, az, dist = (hero - frankfurt).at(ts.utc(2027, 1, 1, 0, 29, 30)).altaz()
print(alt.degrees, az.degrees, dist.km)
```

```
89.2  185.1  555.9
```

- **Altitude (elevation):** degrees above the horizon. 89.2° means almost straight overhead. This is the number our 25° visibility rule checks.
- **Azimuth:** compass direction (0° north, 90° east, 185° roughly south). An antenna would point here.
- **Distance:** 555.9 km, almost exactly the orbit altitude, because it's overhead. Light-travel delay = distance ÷ speed of light ≈ 1.9 ms.
- Used in: `visibility.py` (`elevation_deg`). This is the core of pass prediction.

## 7. Pass finder: `sat.find_events(place, t0, t1, altitude_degrees=...)`

Searches a time window and returns exact rise, peak ("culminate") and set times above a minimum elevation.

```python
times, events = hero.find_events(frankfurt, EPOCH, EPOCH + 0.1, altitude_degrees=25)
for t, e in zip(times, events):
    print(t.utc_strftime('%H:%M:%S'), ['rise', 'culminate', 'set'][e])
```

```
00:27:08 rise
00:29:30 culminate
00:31:51 set
02:08:07 rise
02:08:44 culminate
02:09:21 set
```

- It's more precise than our 30-second grid, because it searches for the exact crossing.
- The second pass (02:08 to 02:09) barely clears 25°: the satellite skimmed the edge of Frankfurt's view.
- Used in: checking `visibility.find_passes()`; our loop agreed within one 30 s step. Our own loop stays because it also produces the per-step elevation the link emulator needs.

## 8. Sun and planets: `load('de421.bsp')`

A file from NASA's Jet Propulsion Laboratory with the positions of the Sun, Moon and planets from 1900 to 2050 (about 17 MB).

```python
eph = load('de421.bsp')   # downloads once, then reads from disk
sun, earth = eph['sun'], eph['earth']
```

- Needed for anything involving sunlight: eclipses, solar panel angle, sun sensors.
- It downloads from JPL on first use. If a network blocks that, `pip install skyfield-data` ships a copy.

## 9. Eclipse: `sat.at(t).is_sunlit(eph)`

True if the satellite is in sunlight, False if it's in Earth's shadow.

```python
times = ts.utc(2027, 1, 1, 0, range(0, 96, 5))   # one orbit, every 5 min
print(hero.at(times).is_sunlit(eph).astype(int).tolist())
```

```
[1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
```

- 7 of 20 samples are dark: about 35 minutes of a 95-minute orbit, matching our estimate.
- Next up: step 4 turns this into eclipse start/end times and the longest eclipse, which sets battery size.

## 10. Real satellites: TLEs

A TLE (two-line element set) is how tracking agencies publish real orbits. Skyfield can load one from CelesTrak or from two strings.

```python
from skyfield.api import EarthSatellite
line1 = '1 25544U 98067A   ...'   # the ISS; copy current lines from celestrak.org
line2 = '2 25544  51.6...'
iss = EarthSatellite(line1, line2, 'ISS', ts)
# or: iss = load.tle_file('https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle')[0]
```

- Everything above (`at`, `altaz`, `find_events`) then works on the real ISS.
- Step 7 uses this to validate our sim: predict ISS passes and compare them with a public pass-prediction site.
- Not run here: the network this was written on blocks CelesTrak, so no output is shown.

## 11. Reference frames: `.frame_xyz(frame)`

The same position expressed in a different coordinate system.

```python
from skyfield.framelib import itrs
print(g.position.km)          # GCRS: inertial, fixed to the stars
print(g.frame_xyz(itrs).km)   # ITRS: fixed to the rotating Earth
```

```
GCRS [ 6905.4  -364.4  -446.7]
ITRS [-1567.1 -6736.3  -428.5]
```

- Same point, same distance from Earth's center, different axes. Inertial frames are for physics (orbits, attitude); Earth-fixed frames are for anything tied to the ground (gateways, maps, Earth's magnetic field).
- Later: attitude control and the simulated magnetometer need both frames.
