# Software Requirements

**Status:** draft v0.1 (2026-11-26). Covers mode management only. Power, comms, attitude control and fault management sections come next.

## Conventions

- **"Shall"** means mandatory. "Should" is not used.
- Each requirement states one behavior, with measurable numbers, and can pass or fail on its own.
- **Verification methods:** **T**est (run and measure against pass/fail), **D**emonstration (run and observe, judged by a person), **A**nalysis (math or simulation), **I**nspection (review code or documents).
- Thresholds marked *(configurable)* are parameters the ground can update; the value shown is the default.

## Mode management (MODE)

| ID | Requirement | Verify |
| --- | --- | --- |
| MODE-001 | In any mode after separation from the launch vehicle, except Deorbit, the flight software shall enter Safe mode within 1 second of battery state of charge falling below 40%. | T |
| MODE-002 | The flight software shall enter Safe mode within 1 second after the third unplanned reset within any 5-minute window. | T |
| MODE-003 | The flight software shall leave Safe mode only on an authenticated ground command. | T |
| MODE-004 | The flight software shall enter Detumble mode between 90 and 120 seconds after separation from the launch vehicle is detected. | T |
| MODE-005 | The flight software shall enter Commissioning mode within 10 seconds after the body rotation rate stays below 0.5°/s for 5 continuous minutes. | T |
| MODE-006 | The flight software shall transition from Commissioning to Nominal only on an authenticated ground command. | T |
| MODE-007 | The flight software shall enter Collision Avoidance mode within 10 seconds after the collision probability, computed from the latest ground-provided conjunction data, exceeds the entry threshold *(configurable, default 1 in 10,000)*. | T |
| MODE-008 | The flight software shall not enter Collision Avoidance mode while the collision probability is at or below the entry threshold. | T |
| MODE-009 | The flight software shall transition from Collision Avoidance to Nominal within 10 seconds after either (a) the collision probability recomputed after the avoidance burn falls below the exit threshold *(configurable, default 1 in 100,000)*, or (b) the predicted time of closest approach has passed. | T |
| MODE-010 | The flight software shall arm deorbit, and report "deorbit armed" in telemetry, within 1 second of receiving an authenticated Arm Deorbit command. | T |
| MODE-011 | The flight software shall disarm deorbit 10 minutes after arming if no authenticated Execute Deorbit command has been received. | T |
| MODE-012 | The flight software shall report "deorbit execute received" in telemetry within 1 second of receiving an authenticated Execute Deorbit command. | T |
| MODE-013 | The flight software shall enter Deorbit mode within 1 second of receiving an authenticated Execute Deorbit command while deorbit is armed. | T |
| MODE-014 | The flight software shall reject an Execute Deorbit command received while deorbit is not armed, and report "execute rejected: not armed" in telemetry. | T |
| MODE-015 | The flight software shall pause the deorbit burn within 1 second of detecting a propulsion, attitude control, or power fault while in Deorbit mode. | T |
| MODE-016 | After pausing the deorbit burn, the flight software shall include its current position, velocity, and predicted orbit in telemetry sent on the next available link (direct or inter-satellite). | T |
| MODE-017 | The flight software shall resume a paused deorbit burn only on an authenticated ground command. | T |

### Still to write

- COMM-001: reject any command that fails authentication (applies to every command, so it belongs in the comms section).
- Commissioning → Safe on a failed subsystem check.
- Collision Avoidance → Safe on a fault mid-burn.

## How these were written: mistakes and what I learned

This was my first set of requirements. Each one was drafted, reviewed and rewritten. These are the mistakes I made and the rule each one taught me.

| Mistake | Example from my draft | Rule learned |
| --- | --- | --- |
| Using "should" | "The flight software should enter commissioning mode..." | "Should" means optional. Mandatory behavior uses "shall." |
| Vague conditions | "...once the satellite is in proper attitude and orbital trajectory" | Every condition needs a number a test can check (rate < 0.5°/s for 5 min). |
| Requiring something that can't be true yet | Requiring the final orbit before Commissioning | Check each condition against the concept of operations. The satellite deliberately starts in a low insertion orbit. |
| Gate without a trigger | "shall not leave Collision Avoidance unless risk is below 1 in 10,000" | "Only when" or "not unless" says when something is *allowed*, not that it *must* happen. Pair it with a positive "shall... within N seconds." |
| One-sided conditions | "enter Collision Avoidance only when probability is above 0.5%" | Write both the "must" side and the "must not" side, as separate requirements. |
| Unrealistic threshold | 0.5% (1 in 200) collision probability | Operators typically act around 1 in 10,000 or lower. Make tunable values ground-configurable. |
| Missing upper bound | "enter Detumble no earlier than 90 seconds after separation" | A lower bound alone is satisfied by never doing it. Give a window (90–120 s). |
| Two behaviors in one requirement | Arming and auto-disarming in one sentence joined by "and" | One behavior per requirement, so each passes or fails on its own. |
| Wrong verification method | Demonstration for a measurable pass/fail outcome | Measurable outcome means Test. Demonstration is for things a person judges. |
| Blocking my own safety rule | "shall not exit Commissioning until ground sign-off" (which also blocked going to Safe) | Name the specific transition. Review requirements as a set, not one at a time: two can each look fine and still contradict. |
| Checking history instead of state | "execute only if an arm command was received in the last 10 minutes" (still fires after a Disarm) | Check the current state ("while armed"), which other requirements define. |
| Missing a mode in the set-level check | Found that Deorbit can't reach Safe, but missed Launch | Walk every row of the modes table. Gaps hide in the modes you think of least. |
| Writing a new requirement for an existing rule | Drafted "enter Safe within 1 s of separation if battery < 40%" | MODE-001 already covered low battery; its scope just needed to say which modes it applies to. Check existing requirements before adding new ones. |
| Vague trigger ("a fault") | "stop all Deorbit activities within 1 second of discovering a fault" | Name the fault classes (propulsion, attitude control, power). |
| Forgetting a lesson from the concept of operations | "report... to ground within 1 second of establishing contact" | The design already says to use any available link, including inter-satellite links. |
| Forgetting the rejection path | No requirement for an Execute that arrives while not armed | Write requirements for what gets rejected, not just what succeeds. |
| Repeating a general rule | "only arm once an authenticated command is received" | Rules that apply to every command (authentication) belong in one general requirement. |
| Mixing up directions | "after sending a 'deorbit execute received' command" | Commands go up from the ground; telemetry comes down from the satellite. |

Recurring patterns to watch: writing "should" (still happening in later drafts), bundling behaviors with "and," and gate-only wording.
