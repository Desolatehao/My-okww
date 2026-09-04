import time

from src.char.BaseChar import BaseChar, SwitchPriority


class Douling(BaseChar):
    """Buling rotation with a dedicated Phrolova/Verina team axis."""

    # The reference Buling implementation uses cycle_sleep()'s 0.1s input
    # cadence, an explicit 0.2s skill tail, a 0.05s jump settle, and a 2.5s
    # heavy-attack hold. These are implementation timings, not video-frame
    # measurements; keep the frame-audit table in TIMING.md as the authority
    # for later replacement.
    AXIS_NORMAL_INTERVAL = 0.10
    AXIS_NORMAL_CAST_TIME = 0.10
    AXIS_AERIAL_NORMAL_INTERVAL = 0.05
    AXIS_AERIAL_NORMAL_CAST_TIME = 0.05
    AXIS_AERIAL_NORMAL_POST_SLEEP = 0.05
    AXIS_SKILL_CAST_TIME = 0.20
    AXIS_LIBERATION_CAST_TIME = 0.0
    AXIS_ECHO_CAST_TIME = 0.0
    AXIS_HEAVY_CAST_TIME = 2.50
    # Phase 3 video timing: each of the two consecutive Z actions is about
    # 0.75s, ending around 00:00:08:690 before the immediate R hand-off.
    AXIS_PHASE3_HEAVY_DURATION = 0.75
    AXIS_PHASE3_HEAVY_GAP = 0.20
    AXIS_PHASE3_HEAVY_POST_GAP = 0.35
    AXIS_SEGMENT1_NORMAL_WINDOW = 1.20
    AXIS_SEGMENT1_FOLLOWUP_NORMAL_WINDOW = 1.00
    # Video timing: startup AA begins around 00:00:00:598 and the switch
    # happens around 00:00:01:198. Keep the actor on field for this full
    # window so the second attack has entered its action before hand-off.
    AXIS_STARTUP_AA_WINDOW = 0.60
    AXIS_STARTUP_SECOND_A_DELAY = 0.30
    # Phase 5 video: Buling stays on field from 18.750 to 20.800 while
    # repeatedly inputting A, then sends Q. Tune the total window only.
    AXIS_PHASE5_AA_DURATION = 2.05
    AXIS_PHASE5_AA_INTERVAL = 0.15
    AXIS_SWITCH_LOCK = 8.0
    AXIS_DODGE_PRE_SLEEP = 0.14
    AXIS_DODGE_POST_SLEEP = 0.12
    AXIS_JUMP_AFTER_SLEEP = 0.01
    AXIS_JUMP_POST_SLEEP = 0.05
    AXIS_SKILL_POST_SLEEP = 0.20
    AXIS_LIBERATION_POST_SLEEP = 0.0
    AXIS_ECHO_POST_SLEEP = 0.0
    AXIS_INTRO_TIMEOUT = 1.2
    AXIS_INTRO_LOCK = 0.90              # provisional; replace after frame audit
    AXIS_INTRO_POST_SLEEP = 0.16
    AXIS_ACTION_RETRY_SLEEP = 0.10
    AXIS_ACTION_WAIT_TIMEOUT = 3.0

    _AXIS_TEAM = {'char_douling', 'char_phrolova', 'char_verina'}
    _AXIS_PHASE_ACTOR = {
        0: 'char_douling',
        1: 'char_verina',
        2: 'char_phrolova',
        3: 'char_douling',
        4: 'char_phrolova',
        5: 'char_douling',
        6: 'char_verina',
        7: 'char_phrolova',
        8: 'char_verina',
        9: 'char_douling',
        10: 'char_verina',
        11: 'char_douling',
        12: 'char_phrolova',
        13: 'char_verina',
        14: 'char_phrolova',
    }
    _AXIS_NEXT = {
        0: (1, 'char_verina', False),
        3: (4, 'char_phrolova', True),
        5: (6, 'char_verina', False),
        9: (10, 'char_verina', False),
        11: (12, 'char_phrolova', True),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._segment = 1

    def do_perform(self):
        if self._axis_enabled():
            return self._do_axis_perform()
        if self._segment == 1:
            self._do_segment1()
        else:
            self._do_segment2()

    def _axis_enabled(self):
        chars = getattr(self.task, 'chars', ()) if self.task is not None else ()
        names = {getattr(char, 'char_name', None) for char in chars if char is not None}
        return names == self._AXIS_TEAM

    def _axis_state(self):
        state = getattr(self.task, '_dpv_axis_state', None)
        if not isinstance(state, dict) or state.get('team') != self._AXIS_TEAM:
            state = {
                'team': set(self._AXIS_TEAM),
                'phase': 0,
                'target': 'char_douling',
                'step': 0,
                'phase_started': False,
                'step_wait_started': None,
            }
            self.task._dpv_axis_state = state
        else:
            state.setdefault('step', 0)
            state.setdefault('phase_started', False)
            state.setdefault('step_wait_started', None)
        return state

    def _axis_sync_phase(self):
        state = self._axis_state()
        if state.get('phase') not in self._AXIS_PHASE_ACTOR:
            state['phase'] = 0
            state['target'] = self._AXIS_PHASE_ACTOR[0]
            state['step'] = 0
            state['phase_started'] = False
            state['step_wait_started'] = None
        return state['phase']

    def _axis_route_to_actor(self, phase):
        actor = self._AXIS_PHASE_ACTOR[phase]
        if self.char_name == actor:
            return False
        state = self._axis_state()
        state['target'] = actor
        self._axis_switch_to(actor)
        return True

    def _axis_switch_to(self, target_name, free_intro=False):
        target = next(
            (char for char in getattr(self.task, 'chars', ())
             if char is not None and getattr(char, 'char_name', None) == target_name),
            None,
        )
        if target is None:
            self.logger.warning(f'dpv axis target not found: {target_name}')
            return False
        source = self
        slot = target.index + 1
        start = time.time()
        last_send = 0.0
        switched = False
        while time.time() - start < 2.0:
            now = time.time()
            if now - last_send >= 0.10:
                self.task.send_key(slot, down_time=0.01)
                last_send = now
            self.task.next_frame()
            in_team, current_index, _ = self.task.in_team()
            if in_team and current_index == target.index:
                switched = True
                break
        if not switched:
            self.logger.warning(f'dpv direct switch failed: {source.char_name} -> {target.char_name}')
            return False
        self.task.in_liberation = False
        source.switch_out(con_full=free_intro)
        target.is_current_char = True
        target.has_intro = free_intro
        target.has_sub_dps_intro = free_intro and source.is_sub_dps
        target.last_switch_in_time = time.time()
        if free_intro:
            now = time.time()
            self.task.add_freeze_duration(now, target.intro_motion_freeze_duration, -100)
            source.last_outro_time = now
        self.logger.info(f'dpv direct switch {source.char_name} -> {target.char_name} free_intro={free_intro}')
        return True

    def _axis_wait_intro(self):
        if self.has_intro:
            started_at = time.perf_counter()
            self.wait_intro(time_out=self.AXIS_INTRO_TIMEOUT, click=False)
            self._axis_wait_cast(started_at, self.AXIS_INTRO_LOCK)
            self.sleep(self.AXIS_INTRO_POST_SLEEP)

    def _axis_advance(self, phase):
        next_phase, target, free_intro = self._AXIS_NEXT[phase]
        state = self._axis_state()
        state['phase'] = next_phase
        state['target'] = target
        state['step'] = 0
        state['phase_started'] = False
        state['step_wait_started'] = None
        self._axis_switch_to(target, free_intro=free_intro)

    def _axis_start_phase(self):
        state = self._axis_state()
        if state['phase_started']:
            return
        self._axis_wait_intro()
        state['phase_started'] = True

    def _axis_run_actions(self, actions):
        """Run a phase from its persistent action cursor."""
        state = self._axis_state()
        step = state['step']
        while step < len(actions):
            action = actions[step]
            started_at = time.perf_counter()
            result = action()
            elapsed = time.perf_counter() - started_at
            self.logger.debug(
                f'dpv axis phase={state["phase"]} step={step} '
                f'action={getattr(action, "__name__", type(action).__name__)} '
                f'elapsed={elapsed:.3f}s result={result}'
            )
            if result is False:
                state['step'] = step
                now = time.perf_counter()
                if state.get('step_wait_started') is None:
                    state['step_wait_started'] = now
                if now - state['step_wait_started'] >= self.AXIS_ACTION_WAIT_TIMEOUT:
                    self.logger.warning(
                        f'dpv axis phase={state["phase"]} step={step} unavailable; skipping')
                    state['step'] = step + 1
                    state['step_wait_started'] = None
                    step += 1
                    continue
                self.sleep(self.AXIS_ACTION_RETRY_SLEEP)
                return False
            step += 1
            state['step'] = step
            state['step_wait_started'] = None
        return True

    def _axis_wait_cast(self, started_at, cast_time):
        remaining = cast_time - (time.perf_counter() - started_at)
        if remaining > 0:
            self.sleep(remaining, check_combat=False)

    def _axis_normal(self, count=1, interval=None, cast_time=None):
        if interval is None:
            interval = self.AXIS_NORMAL_INTERVAL
        if cast_time is None:
            cast_time = self.AXIS_NORMAL_CAST_TIME
        for _ in range(count):
            started_at = time.perf_counter()
            self.check_combat()
            self.click()
            self.task.next_frame()
            self._axis_wait_cast(started_at, max(interval, cast_time))
        return True

    def _axis_startup_two_normal(self):
        """Send two accepted A inputs, then hold the startup window to 0.6s."""
        started_at = time.perf_counter()
        self.check_combat()
        self.click()
        self.task.next_frame()
        delay = self.AXIS_STARTUP_SECOND_A_DELAY - (time.perf_counter() - started_at)
        if delay > 0:
            self.sleep(delay, check_combat=False)
        self.check_combat()
        self.click()
        self.task.next_frame()
        remaining = self.AXIS_STARTUP_AA_WINDOW - (time.perf_counter() - started_at)
        if remaining > 0:
            self.sleep(remaining, check_combat=False)
        return True

    def _axis_phase5_aa_window(self):
        """Keep sending A through the phase-5 total window before Q."""
        started_at = time.perf_counter()
        while time.perf_counter() - started_at < self.AXIS_PHASE5_AA_DURATION:
            self.check_combat()
            self.click()
            self.task.next_frame()
            self.sleep(self.AXIS_PHASE5_AA_INTERVAL, check_combat=False)
        return True

    def _axis_phase3_heavy_followup(self):
        """Let the first phase-3 heavy resolve before starting the second."""
        self.sleep(self.AXIS_PHASE3_HEAVY_GAP, check_combat=False)
        completed = self._axis_heavy(self.AXIS_PHASE3_HEAVY_DURATION)
        if completed:
            self.sleep(self.AXIS_PHASE3_HEAVY_POST_GAP, check_combat=False)
        return completed

    def _axis_jump(self):
        started_at = time.perf_counter()
        self.task.jump(after_sleep=self.AXIS_JUMP_AFTER_SLEEP)
        self.task.next_frame()
        self._axis_wait_cast(
            started_at,
            self.AXIS_JUMP_AFTER_SLEEP + self.AXIS_JUMP_POST_SLEEP,
        )
        return True

    def _axis_heavy(self, duration=None):
        if duration is None:
            duration = self.AXIS_HEAVY_CAST_TIME
        if self.flying():
            self.wait_down()
        completed = self._heavy_attack_hold(duration)
        if not completed:
            self.logger.warning(
                f'dpv axis heavy interrupted phase={self._axis_state().get("phase")}')
        return completed

    def _axis_echo(self):
        if not self.echo_available():
            return False
        started_at = time.perf_counter()
        clicked = self.click_echo(time_out=0)
        if clicked:
            self.task.next_frame()
            self._axis_wait_cast(started_at, self.AXIS_ECHO_CAST_TIME)
            self.sleep(self.AXIS_ECHO_POST_SLEEP, check_combat=False)
        return clicked

    def _axis_resonance(self):
        if not self.resonance_available():
            return False
        started_at = time.perf_counter()
        clicked = self.click_resonance(
            send_click=False,
            time_out=0,
            post_sleep=self.AXIS_SKILL_POST_SLEEP,
        )[0]
        if clicked:
            self.task.next_frame()
            self._axis_wait_cast(started_at, self.AXIS_SKILL_CAST_TIME)
        return clicked

    def _axis_liberation(self):
        if not self.liberation_available():
            return False
        started_at = time.perf_counter()
        clicked = self.click_liberation(wait_if_cd_ready=0)
        if clicked:
            self.task.next_frame()
            self._axis_wait_cast(started_at, self.AXIS_LIBERATION_CAST_TIME)
            self.sleep(self.AXIS_LIBERATION_POST_SLEEP, check_combat=False)
        return clicked

    def _do_axis_perform(self):
        phase = self._axis_sync_phase()
        if self._axis_route_to_actor(phase):
            return
        self._axis_start_phase()
        if phase == 0:  # Startup: Buling aa
            actions = (self._axis_startup_two_normal,)
        elif phase == 3:  # Startup: Buling e aaaa jump a z z r
            actions = (
                self._axis_resonance,
                lambda: self._axis_normal(count=4, interval=0.20),
                self._axis_jump,
                lambda: self._axis_normal(
                    count=1,
                    interval=self.AXIS_AERIAL_NORMAL_INTERVAL,
                    cast_time=self.AXIS_AERIAL_NORMAL_CAST_TIME,
                ),
                lambda: self._axis_heavy(self.AXIS_PHASE3_HEAVY_DURATION),
                self._axis_phase3_heavy_followup,
                self._axis_liberation,
            )
        elif phase == 5:  # Startup: Buling aa q
            actions = (self._axis_phase5_aa_window, self._axis_echo)
        elif phase == 9:  # Loop: Buling e a jump aa z aaaa z
            actions = (self._axis_resonance, self._axis_normal,
                       self._axis_jump,
                       lambda: self._axis_normal(
                           count=2,
                           interval=self.AXIS_AERIAL_NORMAL_INTERVAL,
                           cast_time=self.AXIS_AERIAL_NORMAL_CAST_TIME,
                       ),
                       self._axis_heavy,
                       lambda: self._axis_normal(count=4),
                       self._axis_heavy)
        elif phase == 11:  # Loop: Buling aa q r
            actions = (lambda: self._axis_normal(2),
                       self._axis_echo, self._axis_liberation)
        else:
            actions = ()
        if self._axis_run_actions(actions):
            self._axis_advance(phase)

    def _do_segment1(self):
        self._normal_attack_cycle(self.AXIS_SEGMENT1_NORMAL_WINDOW)
        if self.flying():
            self.wait_down()
        self.check_combat()
        clicked = self.click_resonance(send_click=True, time_out=0.5)[0]
        if not clicked:
            self._finish_and_reset()
            return
        self.sleep(self.AXIS_SKILL_POST_SLEEP)
        if self.flying():
            self.wait_down()
        self.check_combat()
        self._normal_attack_cycle(self.AXIS_SEGMENT1_FOLLOWUP_NORMAL_WINDOW)
        self._segment = 2
        self.switch_next_char()

    def _do_segment2(self):
        self.check_combat()
        self.task.jump(after_sleep=self.AXIS_JUMP_AFTER_SLEEP)
        self.sleep(self.AXIS_JUMP_POST_SLEEP)
        self.check_combat()
        if self.flying():
            self.click()
            self.sleep(self.AXIS_AERIAL_NORMAL_POST_SLEEP)
        else:
            self.wait_down()
        self.check_combat()
        self._heavy_attack_hold(self.AXIS_HEAVY_CAST_TIME)
        self.click_echo(time_out=0)
        self.click_liberation()
        self._segment = 1
        self.switch_next_char()

    def _finish_and_reset(self):
        self.click_echo(time_out=0)
        self.click_liberation()
        self._segment = 1
        self.switch_next_char()

    def _normal_attack_cycle(self, duration):
        start = time.time()
        while time.time() - start < duration:
            self.cycle_start()
            if self.flying():
                self.wait_down()
                break
            self.click()
            self.cycle_sleep()

    def _heavy_attack_hold(self, duration):
        retries = 3
        for _ in range(retries):
            self.check_combat()
            self.task.mouse_down()
            start = time.time()
            interrupted = False
            while time.time() - start < duration:
                if self.flying():
                    interrupted = True
                    break
                self.sleep(0.1)
            self.task.mouse_up()
            self.sleep(0.01)
            if not interrupted:
                return True
            self.wait_down()
        return False

    def reset_state(self):
        super().reset_state()
        self._segment = 1

    def on_combat_end(self, chars):
        if self.task is not None:
            self.task.__dict__.pop('_dpv_axis_state', None)

    def healer_full_con_switch_locked(self):
        if self._axis_enabled():
            return False
        return super().healer_full_con_switch_locked()

    def get_switch_priority(self, current_char=None, has_intro=False, target_low_con=False):
        if self._axis_enabled():
            target = self._axis_state().get('target')
            if target:
                return SwitchPriority.MUST if self.char_name == target else SwitchPriority.NO
        if self.time_elapsed_accounting_for_freeze(self.last_perform) < self.AXIS_SWITCH_LOCK:
            return SwitchPriority.NO
        return SwitchPriority.NORMAL
