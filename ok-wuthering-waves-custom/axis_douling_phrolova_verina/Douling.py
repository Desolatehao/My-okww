import time

from src.char.BaseChar import BaseChar, SwitchPriority


class Douling(BaseChar):
    """Buling rotation with a dedicated Phrolova/Verina team axis."""

    AXIS_NORMAL_INTERVAL = 0.18
    AXIS_DODGE_PRE_SLEEP = 0.14
    AXIS_DODGE_POST_SLEEP = 0.12
    AXIS_JUMP_POST_SLEEP = 0.14
    AXIS_SKILL_POST_SLEEP = 0.22
    AXIS_ECHO_POST_SLEEP = 0.16
    AXIS_INTRO_TIMEOUT = 1.2
    AXIS_INTRO_POST_SLEEP = 0.16

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
        0: (1, 'char_verina'),
        3: (4, 'char_phrolova'),
        5: (6, 'char_verina'),
        9: (10, 'char_verina'),
        11: (12, 'char_phrolova'),
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

    def _axis_jump(self):
        self.task.jump(after_sleep=0.01)
        self.task.next_frame()
        self.sleep(self.AXIS_JUMP_POST_SLEEP)

    def _axis_heavy(self, duration=2.5):
        if self.flying():
            self.wait_down()
        self._heavy_attack_hold(duration)

    def _axis_echo(self):
        if not self.echo_available():
            return False
        clicked = self.click_echo(time_out=0)
        if clicked:
            self.task.next_frame()
            self.sleep(self.AXIS_ECHO_POST_SLEEP)
        return clicked

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

    def _do_axis_perform(self):
        phase = self._axis_sync_phase()
        if self._axis_route_to_actor(phase):
            return
        self._axis_wait_intro()
        if phase == 0:  # Startup: Buling aa
            self._axis_normal(2)
        elif phase == 3:  # Startup: Buling e a z jump a z r
            self._axis_resonance()
            self._axis_normal()
            self._axis_heavy()
            self._axis_jump()
            self._axis_normal()
            self._axis_heavy()
            self._axis_echo()
        elif phase == 5:  # Startup: Buling aa q
            self._axis_normal(2)
            self._axis_liberation()
        elif phase == 9:  # Loop: Buling e a jump a z z
            self._axis_resonance()
            self._axis_normal()
            self._axis_jump()
            self._axis_normal()
            self._axis_heavy()
            self._axis_heavy()
        elif phase == 11:  # Loop: Buling aa q r
            self._axis_normal(2)
            self._axis_liberation()
            self._axis_echo()
        self._axis_advance(phase)

    def _do_segment1(self):
        self._normal_attack_cycle(1.2)
        if self.flying():
            self.wait_down()
        self.check_combat()
        clicked = self.click_resonance(send_click=True, time_out=0.5)[0]
        if not clicked:
            self._finish_and_reset()
            return
        self.sleep(0.2)
        if self.flying():
            self.wait_down()
        self.check_combat()
        self._normal_attack_cycle(1.0)
        self._segment = 2
        self.switch_next_char()

    def _do_segment2(self):
        self.check_combat()
        self.task.jump(after_sleep=0.01)
        self.sleep(0.05)
        self.check_combat()
        if self.flying():
            self.click()
            self.sleep(0.05)
        else:
            self.wait_down()
        self.check_combat()
        self._heavy_attack_hold(2.5)
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
                return
            self.wait_down()

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
        if self.time_elapsed_accounting_for_freeze(self.last_perform) < 8:
            return SwitchPriority.NO
        return SwitchPriority.NORMAL
