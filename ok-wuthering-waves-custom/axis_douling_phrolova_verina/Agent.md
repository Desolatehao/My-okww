# Douling / Phrolova / Verina Axis

## Purpose

This folder is a reviewed snapshot of the targeted three-character rotation for OKWW:

- Douling (`char_douling`, displayed as Buling/卜灵)
- Phrolova (`char_phrolova`, displayed as Phrolova/弗洛洛)
- Verina (`char_verina`, displayed as Verina/维里奈)

The files in this folder are not loaded automatically by OKWW. They are a deliverable snapshot. The runnable customized checkout is the sibling folder `ok-wuthering-waves-custom`; the original `ok-wuthering-waves` checkout is kept unchanged. To run the axis in the customized checkout, the three files are already present in `src/char/`.

## Deployment

For the customized checkout, the direct source-file method is the simplest:

1. Back up `src/char/Douling.py`, `src/char/Phrolova.py`, and `src/char/Verina.py`.
2. Copy the matching three files from this folder into `src/char/`.
3. Restart OKWW so the imported character classes and team-code cache are refreshed.
4. Start Auto Combat with exactly Buling, Phrolova, and Verina in the detected team.

The Qt Character Code tab is the alternative for keeping the change team-scoped. Create or import a custom team containing exactly these three characters, then replace and save the corresponding `Douling.py`, `Phrolova.py`, and `Verina.py` entries. The current `弗卜维.zip` in this folder is preserved as a historical artifact; it does not contain the current `team.json` manifest required by the team importer, so use the loose files above or export a new archive from the Character Code tab.

Do not combine the three classes into one Python file, rename the classes, or replace `BaseChar.py`. The axis gate depends on the canonical names `char_douling`, `char_phrolova`, and `char_verina`.

## Input Notation

- `a` / `A`: normal attack. Uppercase `A` is intentionally treated as the same basic attack click.
- `z` / `Z`: heavy attack, produced by holding the basic attack button.
- `e`: resonance skill, through `click_resonance`.
- `q`: liberation, through `click_liberation`.
- `r`: echo, through `click_echo`.
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

Each phase sets the next phase before calling `switch_next_char`. The expected target returns `SwitchPriority.MUST`; all other team members return `SwitchPriority.NO`. Douling and Verina also disable the base healer full-concerto switch lockout while this exact team is active, because that lockout would otherwise prevent the requested short return to a healer.

The state is removed by `on_combat_end`. Character-local state is reset through `reset_state`, so a new combat starts at phase 0 and routes to Douling.

## Timing Policy

The axis uses explicit action buffers instead of chaining inputs at the minimum polling interval:

- Phrolova A-to-A interval: `0.24s`.
- Douling and Verina A-to-A interval: `0.18s`.
- Phrolova dodge: `0.20s` pre-buffer and `0.12s` post-buffer around one right-click.
- Douling and Verina dodge: `0.14s` pre-buffer and `0.12s` post-buffer around one right-click.
- Skill post-buffer: `0.22s` after a successful E or Q.
- Echo post-buffer: `0.16s` after a successful R.
- Jump post-buffer: `0.14s` after `task.jump`.

The Phrolova A-to-dodge buffer is intentional. A direct `a` followed by a short dodge could cancel the attack before its startup was accepted by the game. Each normal attack also calls `task.next_frame()` so the frame loop observes the input before the next action. These values are class constants so they can be tuned without changing the phase table. If a lower-FPS setup still drops the first A, increase Phrolova's `AXIS_NORMAL_INTERVAL` or `AXIS_DODGE_PRE_SLEEP` together; do not remove the pre-buffer.

Axis resonance calls use `send_click=False` so BaseChar does not inject an undocumented extra normal click while waiting for E. The explicit phase actions remain the source of truth.

## Runtime Checklist

1. Ensure the team contains exactly these three characters and all three have a main echo equipped.
2. Synchronize OKWW's Resonance, Liberation, Echo, Dodge, and Jump mappings with the game.
3. Keep `Use Liberation` enabled; the route explicitly uses `q` at several phases.
4. Keep `Check Levitator` enabled so aerial state checks used by Douling's jump/heavy sequence are available.
5. Set `Verina C2` to `True` only when the Verina is actually C2; this skips the loop phase 13 echo.
6. Restart OKWW after replacing source files or changing custom team code so imported classes and team-code caches are refreshed.
7. Test first against a low-risk target and inspect the combat log if a phase does not switch as expected.

## Verification

The snapshot has passed:

- Python compilation with `python -m compileall` for all three files.
- AST parsing for all three files.
- Static/fake-task phase transition validation, including the initial wrong-active-character case (the latest timing-only test should be rerun before gameplay use).
- Expected phase cycle validation: `0 -> 1 -> 2 -> ... -> 14 -> 8`.

Full project tests were not run in the original environment because `pytest` was unavailable and the system Python lacked the project's `cv2` dependency.

## Maintenance Rules

- Keep the class names exactly `Douling`, `Verina`, and `Phrolova`.
- Preserve the exact canonical team gate so unrelated teams retain their existing rotations.
- Use BaseChar helpers for attacks, skills, echo, jumping, switching, cooldown checks, combat checks, and freeze-aware timing.
- If the rotation changes, update the phase table and the corresponding `_AXIS_NEXT` mappings together.
- Any new character-chain option should be added to the project configuration rather than inferred from unavailable UI state.
