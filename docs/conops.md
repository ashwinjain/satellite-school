# Concept of Operations

**Status:** draft v0.1 (2026-11-26)

## 1. Mission

A scaled-down LEO broadband constellation testbed, inspired by public descriptions of Starlink. Three satellites fly in a ~550 km orbit shell, with two ground gateways and laser inter-satellite links (ISLs). Each satellite serves user terminals on the ground. It routes their traffic to a gateway directly, or through neighboring satellites when no gateway is in view.

In the lab, a laptop runs the world simulator and ground station. One "hero" satellite is a Raspberry Pi 3 flight computer plus an STM32 attitude controller with real sensors and a reaction wheel. Two "lite" satellites are Raspberry Pi Zero 2 W boards running the same flight software, with simulated attitude control.

### Why 550 km

- **Low latency:** about 2 ms one way, versus about 120 ms from geostationary orbit.
- **Debris self-cleanup:** residual drag brings a dead satellite down within about 5 years.
- **Link margin:** about 65 times closer than GEO means roughly 4,000 times less signal loss. That margin buys smaller antennas, lower transmit power, or more data rate.
- **The cost:** each satellite covers only a small area, so coverage needs many satellites.

### Key numbers

| Parameter | Value |
| --- | --- |
| Altitude | ~550 km |
| Orbital period | ~95 min (~15 orbits per day) |
| Eclipse per orbit | up to ~35 min (varies by season) |
| Usable gateway pass | ~4 min at best (above ~25° elevation); ~10 min horizon to horizon |
| Battery depth of discharge, nominal | 20–30% per orbit (stays above ~70–80% charge) |
| Ground track shift per orbit | ~24° west (Earth rotation) |

## 2. A day in the life of Satellite 1 (one orbit)

| Time | Event | What the satellite does | Subsystems involved |
| --- | --- | --- | --- |
| T+0 | Leaves eclipse over the Pacific | Battery at ~75%, its lowest point of the orbit. Points solar panels at the sun and recharges. No gateway in view. | Power, attitude control |
| T+5 | Over the ocean, serving ships and aircraft | No gateway in view, so user traffic is routed over ISLs to the neighbor (ahead or behind) with the best path to a gateway. Routing uses a contact plan: orbits are predictable, so the satellite knows hours ahead which neighbor will see a gateway, and when. | Comms, C&DH |
| T+20 | Gateway pass over Texas (~4 min) | The ground uploads the next stored schedule and contact plan (sometimes a software update). The satellite downlinks telemetry recorded since the last pass. Day to day, the satellite runs on its stored schedule, not on live commands. | Comms, C&DH |
| T+40 | Conjunction warning from the ground | The satellite assesses collision probability (most warnings are false alarms). If it's above the threshold, it plans a small burn hours ahead, because electric thrusters are weak. Attitude control points the thruster, and power must afford the thruster's draw. | Propulsion, attitude control, power |
| T+60 | Enters eclipse | Runs on battery. Heaters keep components above their minimum temperatures without draining the battery: on below one threshold, off above a slightly higher one (hysteresis). | Power, thermal |
| T+80 | Reaction wheel overcurrent | FDIR responds in proportion. **Detect:** current over limit for longer than a set time. **Isolate:** turn the wheel off. **Recover:** switch to the spare wheel, or fall back to magnetorquers for rough pointing. Safe mode only if pointing can't be held. Report the event right away through a neighbor if an ISL is up. Keep it stored, and resend at the next direct pass until acknowledged. | Attitude control, C&DH, comms |
| T+95 | Back to start | Never the same orbit twice: Earth has turned ~24°, so different gateways and users are in view. |  |

### Design principle: design for the worst-case link

The flight software assumes there's no link until the next direct pass. Events are stored, sent in priority order when any link is up, and kept until acknowledged. ISLs and relays are extra paths that sometimes exist. This keeps the bus software valid even for a single satellite with no neighbors.

## 3. Modes

The satellite is always in exactly one mode.

| Mode | Purpose | Enters when | Leaves when |
| --- | --- | --- | --- |
| Launch / deployed | Minimal power on the launch vehicle; boot after separation | Power-on | → Detumble, 90–120 s after separation is detected. → Safe, on low battery after separation |
| Detumble | Slow the random spin after separation using magnetorquers | After Launch, on timer | → Commissioning, once body rate stays < 0.5°/s for 5 min. → Safe, on low battery |
| Commissioning | Check out each subsystem with the ground | Detumble complete (then waits for first pass) | → Nominal, on authenticated ground sign-off only. → Safe, on a failed check or fault |
| Nominal | Serve users, route traffic, keep orbit | Ground sign-off from Commissioning or Safe | → Safe, on a fault it can't fix itself. → Collision Avoidance, on a threat. → Deorbit, on ground command only |
| Collision Avoidance | Pause normal work to point and fire thrusters | Collision probability above the entry threshold (ground-configurable) | → Nominal, when the recomputed probability is below the exit threshold or closest approach has passed. → Safe, on a fault mid-burn |
| Safe | Panels to sun, nonessentials off, wait for ground | Battery < 40%, no ground contact for 24 h, repeated computer resets, or an unrecoverable fault | → Nominal, on authenticated ground command only (even if the fault clears) |
| Deorbit | End of life: lower the orbit until re-entry | Two-step authenticated Arm, then Execute | None (one-way). On a propulsion, attitude or power fault, pauses the burn inside Deorbit, reports its new orbit, and resumes only on ground command |

### Autonomy rule

The satellite may move itself **toward safety** (into Safe or Collision Avoidance) on its own. Moves **toward risk or permanence** (out of Safe, into Nominal, into Deorbit) require an authenticated ground command.

### Faults during deorbit

A burn that stops halfway leaves the satellite in a lower, oval orbit that crosses altitudes where other spacecraft fly (the ISS is around 420 km), and tracking predictions no longer match it. Deorbit has no way back to Nominal, so it has its own paused state:
1. Stop the burn and hold a stable attitude.
2. Report actual position, velocity and predicted orbit on the next available link, so the ground can share it with space-tracking organizations.
3. Keep collision avoidance active if the thrusters still work.
4. Resume only on ground command. If propulsion is dead, drag completes the deorbit, faster now from the lower orbit.

### Arm / execute

Irreversible actions use two steps. **Arm** puts the satellite in a ready state and starts a 10-minute timer. **Execute** is accepted only while armed. The satellite disarms on its own when the timer expires, and the ground can send Disarm at any time. One corrupted packet or operator slip can't trigger the action.

## 4. Open questions

- Exact collision probability thresholds (entry ~1 in 10,000, exit ~1 in 100,000 as starting values).
- Telemetry priority levels for event reports carried over ISLs versus customer traffic.
