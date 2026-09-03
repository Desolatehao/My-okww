import time

from src.char.BaseChar import BaseChar, SwitchPriority


class Verina(BaseChar):
    """Verina rotation with a dedicated Phrolova/Buling team axis."""

    ATTACK_INTERVAL: float = 0.1
    NORMAL_ATTACK_TIME: float = 0.6
    JUMP_ATTACK_TIME: float = 0.5
    HEAVY_ATTACK_TIME: float = 0.7
    RECOVER_TIME: float = 0.8
    FIELD_TIME: float = 6.5
    HEAVY_ATTACK_INTERVAL: float = 8.0

    # The reference Verina configuration uses a 0.1s attack cadence.  Skill
    # and liberation helpers already wait for their UI state; these minimums
    # only cover the short input tail before the next phase action.
    AXIS_NORMAL_INTERVAL = ATTACK_INTERVAL
    AXIS_NORMAL_CAST_TIME = ATTACK_INTERVAL
    AXIS_ECHO_CAST_TIME = 0.0
    AXIS_DODGE_PRE_SLEEP = 0.14
    AXIS_DODGE_POST_SLEEP = 0.12
    AXIS_JUMP_POST_SLEEP = 0.14
    AXIS_SKILL_POST_SLEEP = 0.22
    AXIS_ECHO_POST_SLEEP = 0.16
    AXIS_INTRO_TIMEOUT = 1.2
    AXIS_INTRO_LOCK = 0.90              # BaseChar/reference-package intro floor
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
        1: (2, 'char_phrolova', False),
        6: (7, 'char_phrolova', True),
        8: (9, 'char_douling', False),
        10: (11, 'char_douling', False),
        13: (14, 'char_phrolova', True),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_heavy = -1

    def do_perform(self):
        if self._axis_enabled():
            return self._do_axis_perform()
        self.perform_combat()
        self.switch_next_char()

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

    def _axis_normal(self, count=1, interval=None):
        if interval is None:
            interval = self.AXIS_NORMAL_INTERVAL
        for _ in range(count):
            started_at = time.perf_counter()
            self.check_combat()
            self.click()
            self.task.next_frame()
            self._axis_wait_cast(started_at, max(interval, self.AXIS_NORMAL_CAST_TIME))
        return True

    def _axis_jump(self):
        started_at = time.perf_counter()
        self.task.jump(after_sleep=0.01)
        self.task.next_frame()
        self._axis_wait_cast(started_at, self.AXIS_JUMP_POST_SLEEP)
        return True

    def _axis_dodge(self):
        self.sleep(self.AXIS_DODGE_PRE_SLEEP)
        self.task.next_frame()
        self.task.click(key='right')
        self.sleep(self.AXIS_DODGE_POST_SLEEP)
        return True

    def _axis_resonance(self):
        if not self.resonance_available():
            return False
        clicked = self.click_resonance(
            send_click=False,
            time_out=0,
            post_sleep=self.AXIS_SKILL_POST_SLEEP,
        )[0]
        if clicked:
            self.task.next_frame()
        return clicked

    def _axis_liberation(self):
        if not self.liberation_available():
            return False
        clicked = self.click_liberation(wait_if_cd_ready=0)
        if clicked:
            self.task.next_frame()
            self.sleep(self.AXIS_SKILL_POST_SLEEP)
        return clicked

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

    def _axis_verina_c2(self):
        char_config = getattr(self.task, 'char_config', {})
        return bool(char_config.get('Verina C2', False))

    def _do_axis_perform(self):
        phase = self._axis_sync_phase()
        if self._axis_route_to_actor(phase):
            return
        self._axis_start_phase()
        if phase == 1:  # Startup: Verina e
            actions = (self._axis_resonance,)
        elif phase == 6:  # Startup: Verina e q dodge r jump aa
            actions = (self._axis_resonance, self._axis_echo,
                       self._axis_dodge, self._axis_liberation, self._axis_jump,
                       lambda: self._axis_normal(2))
        elif phase == 8:  # Loop entry: Verina -> Buling
            actions = ()
        elif phase == 10:  # Loop: Verina e q
            actions = (self._axis_resonance, self._axis_echo)
        elif phase == 13:  # Loop: Verina r jump aa
            actions = []
            if not self._axis_verina_c2():
                actions.append(self._axis_liberation)
            actions.extend((self._axis_jump, lambda: self._axis_normal(2)))
            actions = tuple(actions)
        else:
            actions = ()
        if self._axis_run_actions(actions):
            self._axis_advance(phase)

    def perform_combat(self):
        """3A -> 大招 -> E -> 声骸 -> (重击) -> 跳跃 -> 2A; 协奏满/超时则提前结束去切人。"""
        self.start = time.time()

        self.continues_normal_attack(self.NORMAL_ATTACK_TIME)

        for cast_skill in (self.cast_liberation, self.cast_resonance, self.cast_echo):
            if self.should_stop():
                return
            cast_skill()

        if self.should_stop():
            return

        self.task.wait_until(lambda: self.task.in_team()[0], time_out=2.0)
        self.sleep(self.RECOVER_TIME)

        if self.is_mouse_forte_full() and self.can_heavy_attack():
            self.heavy_attack(self.HEAVY_ATTACK_TIME)
            self.last_heavy = time.time()
        self.task.jump(after_sleep=0.01)
        self.continues_normal_attack(self.JUMP_ATTACK_TIME)

    def cast_resonance(self):
        if self.resonance_available():
            self.click_resonance(send_click=True, time_out=0)

    def cast_liberation(self):
        if self.liberation_available():
            self.click_liberation()

    def cast_echo(self):
        if self.echo_available():
            self.click_echo(time_out=0)

    def should_stop(self):
        return self.is_con_full() or self.field_time_out()

    def can_heavy_attack(self):
        return self.time_elapsed_accounting_for_freeze(self.last_heavy) >= self.HEAVY_ATTACK_INTERVAL

    def field_time_out(self):
        return self.time_elapsed_accounting_for_freeze(self.start) >= self.FIELD_TIME

    def reset_state(self):
        super().reset_state()
        self.last_heavy = -1

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
        if has_intro and current_char and current_char.char_name in {'char_hiyuki'}:
            return SwitchPriority.MUST
        return super().get_switch_priority(current_char, has_intro, target_low_con)
