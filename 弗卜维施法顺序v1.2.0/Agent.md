# Douling / Phrolova / Verina Axis

## Purpose

This folder is a reviewed snapshot of the targeted three-character rotation for OKWW:

- Douling (`char_douling`, displayed as Buling/卜灵)
- Phrolova (`char_phrolova`, displayed as Phrolova/弗洛洛)
- Verina (`char_verina`, displayed as Verina/维里奈)

## Character Requirements

- Phrolova: `2+1` configuration, meaning S2/C2 plus her signature weapon.
- Verina: C2 changes only whether the loop needs to cast R. With C2, the loop may skip R; with C0, the same rotation can be reproduced by keeping R in the loop.
- Douling and Verina: only first-rank Fantasy Variation is required.
- These are the tested/target configuration notes for the axis. The scripts do not automatically verify chains, weapons, or Fantasy Variation rank.

The files in this folder are not loaded automatically by OKWW. They are a deliverable snapshot. The runnable customized checkout is the sibling folder `ok-wuthering-waves-custom`; the original `ok-wuthering-waves` checkout is kept unchanged. To run the axis in the customized checkout, the three files are already present in `src/char/`.

## Deployment

For the customized checkout, the direct source-file method is the simplest:

1. Back up `src/char/Douling.py`, `src/char/Phrolova.py`, and `src/char/Verina.py`.
2. Copy the matching three files from this folder into `src/char/`.
3. Restart OKWW so the imported character classes and team-code cache are refreshed.
4. Start Auto Combat with exactly Buling, Phrolova, and Verina in the detected team.

The Qt Character Code tab is the alternative for keeping the change team-scoped. Create or import a custom team containing exactly these three characters, then replace and save the corresponding `Douling.py`, `Phrolova.py`, and `Verina.py` entries. This independent snapshot is version `1.2.0`; use the files in this folder together with `MANUAL_TIMELINE_24FPS.md` and `PROGRESS_1.2.0.md` for the current test baseline. The older archives are preserved as historical artifacts and must not be used for current testing.

Do not combine the three classes into one Python file, rename the classes, or replace `BaseChar.py`. The axis gate depends on the canonical names `char_douling`, `char_phrolova`, and `char_verina`.

## Input Notation

- `a` / `A`: normal attack. Uppercase `A` is intentionally treated as the same basic attack click.
- `z` / `Z`: heavy attack, produced by holding the basic attack button.
- `e`: resonance skill, through `click_resonance`.
- `q`: echo, through `click_echo` (声骸技能; no energy requirement).
- `r`: liberation, through `click_liberation` (共鸣解放; requires energy).
- `闪`: one right-click dodge, through `task.click(key='right')`, with explicit pre/post buffers.
- `跳`: jump, through `task.jump`.
- Skill keys are resolved through OKWW's configured key mappings; the code does not assume the physical letters for `q` and `r`.

## Axis Activation

The dedicated state machine is enabled only when the detected canonical team is exactly:

```text
char_douling, char_phrolova, char_verina
```

Other teams continue to use each character's normal implementation. The route logic forces the expected actor before executing a phase, so the initial active character does not have to be Douling.

## Startup Rotation

The startup phases are:

```text
0  Douling:   aa
1  Verina:    e
2  Phrolova:  aa q a e a z
3  Douling:   e a z jump a z r
4  Phrolova:  a dodge a r
5  Douling:   aa q
6  Verina:    e q dodge r jump aa
7  Phrolova:  a dodge a e a dodge
               3a dodge a dodge
               3a dodge a dodge
               3a dodge a dodge
               3a q a z r
8  Verina:    no attack; immediately route to the loop entry
```

## Loop Rotation

The loop phases are:

```text
8   Verina:    no attack; route to Douling
9   Douling:   e a jump a z z
10  Verina:    e q
11  Douling:   aa q r
12  Phrolova:  a dodge a e a
13  Verina:    r jump aa
14  Phrolova:  a dodge a
                3a dodge a dodge
                3a dodge a dodge
                3a q a e a z r
8   Verina:    no attack; route to Douling
```

For a Verina C2 setup, phase 13 can skip `r` when `task.char_config['Verina C2']` is true. The repository `config.py` exposes this option and defaults it to `False`, so the default behavior remains the non-C2 route and phase 13 still attempts `r`.

## State Machine

The three classes share a task-level dictionary named `_dpv_axis_state`:

- `team`: canonical team-name set used to validate the route.
- `phase`: current phase number.
- `target`: canonical name of the next character to switch to.
- `step`: action index within the current phase.
- `phase_started`: whether the intro wait and combo initialization for the current phase have run.

Each phase sets the next phase and resets `step` before calling `switch_next_char`. An action that returns `False` leaves `step` unchanged and is retried on the next combat-loop tick; completed actions are not replayed. The expected target returns `SwitchPriority.MUST`; all other team members return `SwitchPriority.NO`. Douling and Verina also disable the base healer full-concerto switch lockout while this exact team is active, because that lockout would otherwise prevent the requested short return to a healer.

The state is removed by `on_combat_end`. Character-local state is reset through `reset_state`, so a new combat starts at phase 0 and routes to Douling.

## Timing Policy

The axis waits for an action's minimum cast/derive time before issuing the next distinct input. Each wait is anchored immediately before its helper; blocking framework helpers consume that window, so their elapsed time is not double-counted.
Each completed or failed action emits a debug record with its phase, step, callable name, elapsed wall time, and result, so real-game tuning can distinguish a slow helper from an unavailable skill.

| Character | Action | Current timing source |
| --- | --- | --- |
| Phrolova | normal A1/A2/A3 | `0.67 / 0.60 / 0.53s` derive points from the supplied frame data |
| Phrolova | enhanced A | `1.33s` derive point from the supplied frame data |
| Phrolova | E | `0.53s` derive point |
| Phrolova | enhanced E (if explicitly chained) | `1.17s` derive point; not a separate token in the current target axis |
| Phrolova | Q (liberation) | `3.30s` animation fallback; `click_liberation` normally waits for HUD recovery |
| Phrolova | R (echo) | `0s` cast plus `0.16s` input tail; the supplied reference treats echo as hand-off |
| Douling | normal input | reference implementation cadence `0.10s`; this is not a per-attack frame measurement |
| Douling | E | reference implementation tail `0.20s` after `click_resonance` |
| Douling | Q (echo) | no extra fixed tail; `click_echo(time_out=0)` |
| Douling | R (liberation) | framework team-state recovery; used at the scripted R position |
| Douling | jump settle / aerial normal | `0.01s` jump input tail + `0.05s` settle, then `0.05s` after the aerial normal input |
| Douling | heavy | reference `2.5s` hold; interrupted airborne holds retry up to three times |
| Verina | normal A | `0.1s` cadence from `Hiyuki_Lucilla_Verina_a38999_1.0.0.zip` |
| Verina | E | framework state wait plus `0.22s` tail |
| Verina | Q (echo) | `click_echo(time_out=0)` |
| Verina | R (liberation) | framework team-state recovery |

Phrolova's `A` notation is still one normal-attack click; it selects the longer enhanced-action window. Each attack calls `task.next_frame()` so the frame loop observes the input before the next action. The `0.06s` Phrolova interval is only a lower bound; the derive times dominate. In version 1.0.6, ordinary dodge-to-enhanced-A uses a `0.12s` pre-buffer plus a `0.04s` tail, with the A queued during dodge; chain sections use a separate `0.55s` settle window. Phrolova's Z is currently `1.33s` from the manual 24 FPS observation, not the older reference-package `2.32s` value, and remains subject to in-game validation. Douling's values above come from the supplied Augusta/Baizhi/Buling reference implementation, not video frame extraction; update `TIMING.md` and the `AXIS_*` constants when a newer frame audit is available.

Phrolova combo state is also timing-sensitive: manual entry starts the first explicit `a` at A1, while a variation intro reuses A2 and leaves the next explicit `a` at A3. After an enhanced basic attack, the next normal chain starts at A1 again. This is why the implementation tracks A1/A2/A3 instead of applying one fixed delay to every `a`.

Axis resonance calls use `send_click=False` so BaseChar does not inject an undocumented extra normal click while waiting for E. The explicit phase actions remain the source of truth.

## Runtime Checklist

1. Ensure the team contains exactly these three characters and all three have a main echo equipped.
2. Synchronize OKWW's Resonance, Liberation, Echo, Dodge, and Jump mappings with the game.
3. Keep `Use Liberation` enabled; the route explicitly uses `r` at several phases. `q` is the echo key in this setup.
4. Keep `Check Levitator` enabled so aerial state checks used by Douling's jump/heavy sequence are available.
5. Set `Verina C2` to `True` only when the Verina is actually C2; this skips the loop phase 13 echo.
6. Restart OKWW after replacing source files or changing custom team code so imported classes and team-code caches are refreshed.
7. Test first against a low-risk target and inspect the combat log if a phase does not switch as expected.

## Verification

The snapshot has passed:

- Python compilation with `python -m compileall` for all three files.
- AST parsing for all three files.
- Static/fake-task timing validation for Phrolova attack windows and the corrected `3a dodge A dodge` sub-sequence.
- Virtual-clock validation that derive waits top up framework helper time instead of double-counting it.
- Transition, exact-team gate, and exclusive switch-priority validation for every phase boundary.
- Expected phase cycle validation: `0 -> 1 -> 2 -> ... -> 14 -> 8`.

Full project tests were not run in the original environment because `pytest` was unavailable and the system Python lacked the project's `cv2` dependency.

## Manual Test Result (2026-09-04)

The current snapshot was manually verified in OKWW with the exact Buling/Phrolova/Verina team. The latest checks confirmed:

- Phase 0 Buling `AA` now sends the second input after a real input window and holds the actor for about `0.60s` before switching, so both attacks can enter their actions and produce the expected Forte state.
- Phase 3 Buling now follows `E -> 4A -> jump -> aerial A -> Z -> Z -> R`; the observed Forte order before Z is `Gen, Zhen, Zhen, Zhen`, both Z actions trigger, and R no longer interrupts the second Z.
- Phase 6 Verina's final `AA` uses a delayed second input and a `0.80s` hand-off window; both attacks complete before switching to Phrolova.
- Phrolova's scripted R completed and the axis immediately handed off to the next character without the previous multi-second target-search pause.

## Troubleshooting History

- The first persistent-step implementation retried unavailable Q/E/R actions forever or for a long timeout; mandatory actions must not be silently skipped into a later phase.
- The local setup uses `Q = echo` and `R = liberation`. Reversing these mappings makes phase 2 appear to stop after two A inputs because the code waits for a charged liberation in the Q slot.
- `switch_next_char()` performs framework target selection and combat/target checks. During liberation or echo animations the target HUD can disappear, producing `target lost` and an apparent pause.
- Axis hand-offs therefore use the reference package's direct slot-switch pattern: send the numeric slot key, confirm the active slot with `in_team()` without middle-click retargeting, then perform the same character state bookkeeping as `switch_next_char()`.
- Do not update `is_current_char` or `has_intro` before the slot switch is confirmed; doing so desynchronizes the framework from the game and is worse than waiting.

## Maintenance Rules

- Keep the class names exactly `Douling`, `Verina`, and `Phrolova`.
- Preserve the exact canonical team gate so unrelated teams retain their existing rotations.
- Use BaseChar helpers for attacks, skills, echo, jumping, switching, cooldown checks, combat checks, and freeze-aware timing.
- If the rotation changes, update the phase table and the corresponding `_AXIS_NEXT` mappings together.
- Any new character-chain option should be added to the project configuration rather than inferred from unavailable UI state.
- Character-code comments should be written in Chinese and identify the phase, unit, and meaning of each phase-specific parameter.
- Comment-only documentation updates must preserve executable tokens, parameter values, action order, and state-machine behavior.

## Version 1.2.0 Snapshot Update

- `Douling.py`, `Phrolova.py`, and `Verina.py` now include Chinese comments for the axis parameters, phase routes, shared state fields, and action helpers.
- The comments distinguish `q`/`r` key notation from the functional names 声骸 and 共鸣解放; key bindings remain controlled by OKWW configuration.
- The documentation update does not change runtime logic or parameter values. Python AST parsing and executable-token comparison were used to verify this.
