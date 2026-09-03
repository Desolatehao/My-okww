import time

from src.char.BaseChar import BaseChar, SwitchPriority


class Phrolova(BaseChar):
    """Phrolova rotation with a dedicated Buling/Verina team axis."""

    # The reference character script uses a 0.06s input cadence, but the
    # game does not accept the next distinct action until the current attack's
    # derive point. Keep both values explicit: the interval is a lower bound,
    # while the cast times below protect each action boundary.
    AXIS_NORMAL_INTERVAL = 0.06
    AXIS_NORMAL_CAST_TIMES = (0.67, 0.60, 0.53)  # A1/A2/A3 derive points
    AXIS_ENHANCED_CAST_TIME = 1.33               # enhanced basic attack
    AXIS_SKILL_CAST_TIME = 0.53                  # E derive point
    AXIS_LIBERATION_CAST_TIME = 3.30             # Q animation fallback
    AXIS_ECHO_CAST_TIME = 0.0                    # R is a hand-off echo
    AXIS_DODGE_PRE_SLEEP = 0.20
    AXIS_DODGE_POST_SLEEP = 0.12
    AXIS_JUMP_POST_SLEEP = 0.14
    AXIS_SKILL_POST_SLEEP = 0.0
    AXIS_ECHO_POST_SLEEP = 2.0
    AXIS_INTRO_TIMEOUT = 1.2
    AXIS_INTRO_LOCK = 1.30
    AXIS_INTRO_POST_SLEEP = 0.16
    AXIS_ACTION_RETRY_SLEEP = 0.10
    # UI availability checks can lag briefly after a character switch or
    # animation. Do not let one unavailable optional action deadlock the axis.
    AXIS_ACTION_WAIT_TIMEOUT = 3.0
    AXIS_LIBERATION_WAIT_TIMEOUT = 10.0
    AXIS_HEAVY_DURATION = 2.32                  # heavy unlocks Q at frame 139

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
        2: (3, 'char_douling', False),
        4: (5, 'char_douling', True),
        7: (8, 'char_verina', True),
        12: (13, 'char_verina', False),
        14: (8, 'char_verina', True),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_liberation = -1
        self.sp = False
        self.res_ready = False
        self._axis_attack_index = 0

    def skip_combat_check(self):
        return self.time_elapsed_accounting_for_freeze(self.last_liberation) < 2

    def do_perform(self):
        if self._axis_enabled():
            return self._do_axis_perform()
        self._do_default_perform()

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
        """Directly switch by slot, bypassing target search and switch chooser."""
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
        self.logger.info(
            f'dpv direct switch {source.char_name} -> {target.char_name} '
            f'free_intro={free_intro}')
        return True

    def _axis_wait_intro(self):
        if self.has_intro:
            started_at = time.perf_counter()
            # Do not inject unplanned A inputs while the intro animation is
            # still locking the character.  The phase table owns all attacks.
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
        # A variation intro reuses Phrolova's A2 and leaves the next explicit
        # basic attack at A3.  Manual entry starts from A1.
        self._axis_attack_index = 2 if self.has_intro else 0
        state['phase_started'] = True

    def _axis_run_actions(self, actions):
        """Run a phase from its persistent action cursor.

        A failed skill/echo remains the current step, so a later combat-loop
        tick retries it without replaying already completed inputs.
        """
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
                waited = now - state['step_wait_started']
                if waited >= self.AXIS_ACTION_WAIT_TIMEOUT:
                    self.logger.warning(
                        f'dpv axis phase={state["phase"]} step={step} '
                        f'action unavailable for {waited:.1f}s; skipping'
                    )
                    state['step'] = step + 1
                    state['step_wait_started'] = None
                    step += 1
                    continue
                self.sleep(self.AXIS_ACTION_RETRY_SLEEP, check_combat=False)
                return False
            step += 1
            state['step'] = step
            state['step_wait_started'] = None
        return True

    def _axis_wait_cast(self, started_at, cast_time):
        remaining = cast_time - (time.perf_counter() - started_at)
        if remaining > 0:
            # During a liberation/echo animation the target HUD can vanish;
            # combat detection must not abort the hand-off in that window.
            self.sleep(remaining, check_combat=False)

    def _axis_normal(self, count=1, interval=None):
        if interval is None:
            interval = self.AXIS_NORMAL_INTERVAL
        for _ in range(count):
            started_at = time.perf_counter()
            self.click()
            self.task.next_frame()
            cast_time = self.AXIS_NORMAL_CAST_TIMES[
                self._axis_attack_index % len(self.AXIS_NORMAL_CAST_TIMES)
            ]
            self._axis_attack_index += 1
            self._axis_wait_cast(started_at, max(interval, cast_time))
        return True

    def _axis_enhanced(self):
        started_at = time.perf_counter()
        self.click()
        self.task.next_frame()
        self._axis_wait_cast(started_at, self.AXIS_ENHANCED_CAST_TIME)
        # The enhanced basic attack ends the current normal chain.  The next
        # explicit `a` therefore starts at A1, matching the reference axis.
        self._axis_attack_index = 0
        return True

    def _axis_three_normal_dodge(self):
        self._axis_normal(3)
        self._axis_dodge()
        self._axis_enhanced()
        self._axis_dodge()
        return True

    def _axis_dodge(self):
        self.sleep(self.AXIS_DODGE_PRE_SLEEP)
        self.task.next_frame()
        self.task.click(key='right')
        self.sleep(self.AXIS_DODGE_POST_SLEEP)
        return True

    def _axis_jump(self):
        self.task.jump(after_sleep=0.01)
        self.task.next_frame()
        self.sleep(self.AXIS_JUMP_POST_SLEEP)
        return True

    def _axis_heavy(self, duration=None):
        if duration is None:
            duration = self.AXIS_HEAVY_DURATION
        if self.flying():
            self.wait_down()
        self.heavy_attack(duration)
        return True

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
        # This fixed axis must not branch on the unreliable Q icon OCR. Send
        # the configured key at the scripted position and let the game accept
        # it when energy is ready; never wait here and never skip into another
        # phase because the icon was not detected.
        started_at = time.perf_counter()
        self.send_liberation_key()
        self.record_liberation_use()
        self.task.next_frame()
        self._axis_wait_cast(started_at, self.AXIS_LIBERATION_CAST_TIME)
        self.sleep(self.AXIS_SKILL_POST_SLEEP, check_combat=False)
        return True

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

    def _do_axis_perform(self):
        self.last_liberation = -1
        phase = self._axis_sync_phase()
        if self._axis_route_to_actor(phase):
            return
        self._axis_start_phase()
        if phase == 2:  # Startup: Phrolova aa q A e A z
            actions = (
                lambda: self._axis_normal(2), self._axis_echo,
                self._axis_enhanced, self._axis_resonance,
                self._axis_enhanced, self._axis_heavy,
            )
        elif phase == 4:  # Startup: Phrolova a dodge A r
            actions = (self._axis_normal, self._axis_dodge,
                       self._axis_enhanced, self._axis_liberation)
        elif phase == 7:  # Startup: Phrolova a dodge A e A dodge 3a dodge A dodge 3a dodge A dodge 3a q A z r
            actions = (
                self._axis_normal, self._axis_dodge, self._axis_enhanced,
                self._axis_resonance, self._axis_enhanced, self._axis_dodge,
                self._axis_three_normal_dodge, self._axis_three_normal_dodge,
                self._axis_three_normal_dodge, self._axis_three_normal_dodge,
                lambda: self._axis_normal(3),
                self._axis_echo, self._axis_enhanced,
                self._axis_heavy, self._axis_liberation,
            )
        elif phase == 12:  # Loop: Phrolova a dodge A e A
            actions = (self._axis_normal, self._axis_dodge,
                       self._axis_enhanced, self._axis_resonance,
                       self._axis_enhanced)
        elif phase == 14:  # Loop: Phrolova a dodge A 3a dodge A dodge 3a dodge A dodge 3a q A e A z r
            actions = (
                self._axis_normal, self._axis_dodge, self._axis_enhanced,
                self._axis_three_normal_dodge, self._axis_three_normal_dodge,
                 lambda: self._axis_normal(3), self._axis_echo,
                self._axis_enhanced, self._axis_resonance,
                 self._axis_enhanced, self._axis_heavy, self._axis_liberation,
            )
        else:
            actions = ()
        if self._axis_run_actions(actions):
            self._axis_advance(phase)

    def _do_default_perform(self):
        self.last_liberation = -1
        perform_under_outro = False
        self.sp = False
        if self.has_intro:
            self.res_ready = False
            if self.check_outro() in {'char_cantarella'}:
                perform_under_outro = True
            self.continues_normal_attack(1.7)
            self.continues_right_click(0.1)
        if self.flying():
            self.wait_down()
        if self.liberation_available() and self.click_liberation(wait_if_cd_ready=0):
            return self.switch_next_char()
        if self.heavy_and_liber():
            return self.switch_next_char()
        if self.resonance_available() or self.res_ready:
            self.continues_normal_attack(0.1)
            self.click_resonance()
            self.continues_normal_attack(0.1)
            self.task.wait_until(lambda: not self.resonance_available(), post_action=self.task.click, time_out=0.3)
            if not self.click_echo():
                self.continues_right_click(0.1)
        self.res_ready = False
        start = time.time()
        timeout = lambda: time.time() - start < 4
        if perform_under_outro:
            timeout = lambda: self.time_elapsed_accounting_for_freeze(self.last_perform) < 16
            self.sp = True
        while timeout():
            if self.liberation_available() and self.click_liberation(wait_if_cd_ready=0):
                return self.switch_next_char()
            if self.flying():
                self.shorekeeper_auto_dodge()
            if self.heavy_and_liber():
                return self.switch_next_char()
            if self.resonance_available() and 1 < time.time() - start:
                if perform_under_outro:
                    self.continues_normal_attack(0.3)
                    if self.click_resonance()[0]:
                        self.continues_normal_attack(0.1)
                        self.task.wait_until(lambda: not self.resonance_available(), post_action=self.task.click,
                                             time_out=0.3)
                        if not self.click_echo():
                            self.continues_right_click(0.1)
                else:
                    self.res_ready = True
                    break
            self.task.click()
            self.check_combat()
            self.task.next_frame()
        self.switch_next_char()

    def _cantarella_outro_ready(self, current_char, has_intro):
        return self.time_elapsed_accounting_for_freeze(
            self.last_liberation) > 14 and has_intro and current_char and current_char.char_name in {'char_cantarella'}

    def get_switch_priority(self, current_char=None, has_intro=False, target_low_con=False):
        if self._axis_enabled():
            target = self._axis_state().get('target')
            if target:
                return SwitchPriority.MUST if self.char_name == target else SwitchPriority.NO
        self.logger.debug(f'Phrolova last_liberation {self.time_elapsed_accounting_for_freeze(self.last_liberation)}')
        if self._cantarella_outro_ready(current_char, has_intro):
            return SwitchPriority.MUST
        if self.time_elapsed_accounting_for_freeze(self.last_liberation) < 24:
            return SwitchPriority.NO
        return super().get_switch_priority(current_char, has_intro, target_low_con)

    def resonance_available(self):
        if self.sp:
            return not (self.flying() or self.has_cd('resonance'))
        return super().resonance_available()

    def heavy_and_liber(self):
        if self.heavy_click_forte(check_fun=self.is_mouse_forte_full):
            self.logger.debug('Phrolova heavy_click_forte')
            self.task.wait_until(lambda: self.click_liberation(wait_if_cd_ready=0), time_out=3)
            return True

    def shorekeeper_auto_dodge(self):
        from src.char.ShoreKeeper import ShoreKeeper
        for char in self.task.chars:
            if isinstance(char, ShoreKeeper):
                return char.auto_dodge(condition=self.flying)

    def reset_state(self):
        super().reset_state()
        self.sp = False
        self.res_ready = False
        self._axis_attack_index = 0

    def on_combat_end(self, chars):
        if self.task is not None:
            self.task.__dict__.pop('_dpv_axis_state', None)
