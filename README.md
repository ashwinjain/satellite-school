# Satellite School

A hardware-in-the-loop testbed for a scaled-down, Starlink-inspired LEO broadband constellation: three satellites, two ground gateways and simulated inter-satellite links. The flight software is written from scratch to learn satellite bus flight software end to end.

**Status:** Phase 0, mission design and requirements.

- [Concept of operations](docs/conops.md)
- [Software requirements](docs/requirements.md)
- [Skyfield guide](docs/skyfield-guide.md)

## Running the world sim

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m world_sim.demo_orbits
python -m world_sim.demo_passes
```
