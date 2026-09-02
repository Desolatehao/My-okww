import time

from src.char.BaseChar import BaseChar, SwitchPriority


class Phrolova(BaseChar):
    """Phrolova rotation with a dedicated Buling/Verina team axis."""

    AXIS_NORMAL_INTERVAL = 0.24
    AXIS_DODGE_PRE_SLEEP = 0.20
    AXIS_DODGE_POST_SLEEP = 0.12
    AXIS_JUMP_POST_SLEEP = 0.14
    AXIS_SKILL_POST_SLEEP = 0.22
    AXIS_ECHO_POST_SLEEP = 0.16
    AXIS_INTRO_TIMEOUT = 1.2
    AXIS_INTRO_POST_SLEEP = 0.16
    AXIS_HEAVY_DURATION = 0.75

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
        2: (3, 'char_douling'),
        4: (5, 'char_douling'),
        7: (8, 'char_verina'),
        12: (13, 'char_verina'),
        14: (8, 'char_verina'),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_liberation = -1
        self.sp = False
        self.res_ready = False

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
            }
            self.task._dpv_axis_state = state
        return state

    def _axis_sync_phase(self):
        state = self._axis_state()
        if state.get('phase') not in self._AXIS_PHASE_ACTOR:
            state['phase'] = 0
        return state['phase']

    def _axis_route_to_actor(self, phase):
        actor = self._AXIS_PHASE_ACTOR[phase]
        if self.char_name == actor:
            return False
        state = self._axis_state()
        state['target'] = actor
        self.switch_next_char()
        return True

    def _axis_wait_intro(self):
        if self.has_intro:
            self.wait_intro(time_out=self.AXIS_INTRO_TIMEOUT, click=True)
            self.sleep(self.AXIS_INTRO_POST_SLEEP)

    def _axis_advance(self, phase):
        next_phase, target = self._AXIS_NEXT[phase]
        state = self._axis_state()
        state['phase'] = next_phase
        state['target'] = target
        self.switch_next_char()

    def _axis_normal(self, count=1, interval=None):
        if interval is None:
            interval = self.AXIS_NORMAL_INTERVAL
        for _ in range(count):
            self.check_combat()
            self.click()
            self.task.next_frame()
            self.sleep(interval)

    def _axis_three_normal_dodge(self):
        self._axis_normal(3)
        self._axis_dodge()
        self._axis_normal()
        self._axis_dodge()

    def _axis_dodge(self):
        self.sleep(self.AXIS_DODGE_PRE_SLEEP)
        self.task.next_frame()
        self.task.click(key='right')
        self.sleep(self.AXIS_DODGE_POST_SLEEP)

    def _axis_jump(self):
        self.task.jump(after_sleep=0.01)
        self.task.next_frame()
        self.sleep(self.AXIS_JUMP_POST_SLEEP)

    def _axis_heavy(self, duration=None):
        if duration is None:
            duration = self.AXIS_HEAVY_DURATION
        if self.flying():
            self.wait_down()
        self.heavy_attack(duration)

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
        clicked = self.click_echo(time_out=0)
        if clicked:
            self.task.next_frame()
            self.sleep(self.AXIS_ECHO_POST_SLEEP)
        return clicked

    def _do_axis_perform(self):
        self.last_liberation = -1
        phase = self._axis_sync_phase()
        if self._axis_route_to_actor(phase):
            return
        self._axis_wait_intro()
        if phase == 2:  # Startup: Phrolova aa q A e A z
            self._axis_normal(2)
            self._axis_liberation()
            self._axis_normal()
            self._axis_resonance()
            self._axis_normal()
            self._axis_heavy()
        elif phase == 4:  # Startup: Phrolova a dodge A r
            self._axis_normal()
            self._axis_dodge()
            self._axis_normal()
            self._axis_echo()
        elif phase == 7:  # Startup: Phrolova a dodge A e A dodge 3a dodge A dodge 3a dodge A dodge 3a q A z r
            self._axis_normal()
            self._axis_dodge()
            self._axis_normal()
            self._axis_resonance()
            self._axis_normal()
            self._axis_dodge()
            self._axis_three_normal_dodge()
            self._axis_three_normal_dodge()
            self._axis_three_normal_dodge()
            self._axis_normal(3)
            self._axis_liberation()
            self._axis_normal()
            self._axis_heavy()
            self._axis_echo()
        elif phase == 12:  # Loop: Phrolova a dodge A e A
            self._axis_normal()
            self._axis_dodge()
            self._axis_normal()
            self._axis_resonance()
            self._axis_normal()
        elif phase == 14:  # Loop: Phrolova a dodge A 3a dodge A dodge 3a dodge A dodge 3a q A e A z r
            self._axis_normal()
            self._axis_dodge()
            self._axis_normal()
            self._axis_three_normal_dodge()
            self._axis_three_normal_dodge()
            self._axis_normal(3)
            self._axis_liberation()
            self._axis_normal()
            self._axis_resonance()
            self._axis_normal()
            self._axis_heavy()
            self._axis_echo()
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

    def on_combat_end(self, chars):
        if self.task is not None:
            self.task.__dict__.pop('_dpv_axis_state', None)
