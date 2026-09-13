import time

from src.char.BaseChar import BaseChar, SwitchPriority


class Phrolova(BaseChar):
    """Phrolova rotation with a dedicated Buling/Verina team axis."""

    # 以下参数服务于弗洛洛专属轴；单位为秒，括号中的 phase 表示实际使用阶段。
    # The reference character script uses a 0.06s input cadence, but the
    # game does not accept the next distinct action until the current attack's
    # derive point. Keep both values explicit: the interval is a lower bound,
    # while the cast times below protect each action boundary.
    AXIS_NORMAL_INTERVAL = 0.06  # 通用/phase 2、4、7、12、14：普攻输入下限。
    AXIS_NORMAL_CAST_TIMES = (0.67, 0.60, 0.53)  # 通用：A1/A2/A3 各自的可接动作窗口。
    AXIS_ENHANCED_CAST_TIME = 1.33  # 通用：独立强化 A 的完整动作窗口。
    # In the reference video the enhanced A is queued during dodge and the
    # dodge cancels part of its startup/recovery. Keep this shorter window
    # separate from standalone enhanced attacks used outside dodge chains.
    AXIS_DODGE_ENHANCED_DELAY = 0.04  # phase 4、7、12、14：闪避期间预输入强化 A 的延迟。
    # 24 FPS reference: dodge -> enhanced A is about 6 frames.  Chained
    # 3A sections need a slightly longer settle before the next dodge.
    AXIS_DODGE_ENHANCED_CAST_TIME = 0.25  # phase 4、12：普通闪避接强化 A 的窗口。
    AXIS_CHAIN_DODGE_ENHANCED_CAST_TIME = 0.55  # phase 7、14：3A 链闪避接强化 A 的窗口。
    # Phase 2 video: Q is followed by the first enhanced A after roughly
    # 0.9s; each enhanced A remains on field for about 0.55s before the next
    # distinct input is accepted. The final Z input is handed off while its
    # animation continues, so only a short hold is needed here.
    AXIS_PHASE2_Q_TO_A_DELAY = 0.90  # phase 2：声骸后到第一发强化 A 的等待。
    AXIS_PHASE2_ENHANCED_CAST_TIME = 0.55  # phase 2：两发强化 A 之间的动作窗口。
    AXIS_PHASE2_HEAVY_DURATION = 0.3  # phase 2：Z 输入保持时间，之后立即切人。
    # Phase 7 video: one 3A segment lasts about 1.26s. During that window,
    # send a normal-A input every 0.10s; only the total duration is tuned.
    AXIS_PHASE7_THREE_A_DURATION = 1.70  # phase 7/14：一段 3A 连续输入的总窗口。
    AXIS_PHASE7_THREE_A_INTERVAL = 0.10  # phase 7/14：3A 窗口内每次普通 A 的输入间隔。
    AXIS_PHASE7_ECHO_POST_SLEEP = 1.00  # phase 7：Q 动画结束后的强化 A 衔接等待。
    AXIS_PHASE7_Q_TO_A_CAST_TIME = 0.10  # phase 7/14：声骸后接强化 A 的短等待。
    AXIS_PHASE7_Z_TO_R_DELAY = 1.75  # phase 7/14：Z 完成后到共鸣解放的实机衔接等待。
    AXIS_SKILL_CAST_TIME = 0.53  # phase 7、12、14：E 的派生动作窗口。
    AXIS_LIBERATION_CAST_TIME = 3.30  # phase 4、7、14：共鸣解放的动画兜底等待。
    AXIS_ECHO_CAST_TIME = 0.0  # phase 2、7、14：声骸为脱手动作。
    AXIS_DODGE_PRE_SLEEP = 0.12  # phase 4、7、12、14：闪避前置等待。
    AXIS_DODGE_POST_SLEEP = 0.04  # phase 4、7、12、14：闪避后的短衔接等待。
    AXIS_JUMP_POST_SLEEP = 0.14  # 跳跃后到下一输入的稳定等待。
    AXIS_SKILL_POST_SLEEP = 0.0  # E helper 后不额外追加固定等待。
    AXIS_ECHO_POST_SLEEP = 2.0  # 声骸后 HUD/动画恢复的保护等待。
    AXIS_INTRO_TIMEOUT = 1.2  # 变奏入场检测最多等待时间。
    AXIS_INTRO_LOCK = 1.30  # 变奏入场后动作锁定的安全窗口。
    AXIS_INTRO_POST_SLEEP = 0.16  # 入场锁定结束后的额外缓冲。
    AXIS_ACTION_RETRY_SLEEP = 0.10  # 动作暂不可用时的重试间隔。
    # UI availability checks can lag briefly after a character switch or
    # animation. Do not let one unavailable optional action deadlock the axis.
    AXIS_ACTION_WAIT_TIMEOUT = 1.5  # 普通动作持续不可用时的最大等待。
    AXIS_LIBERATION_WAIT_TIMEOUT = 10.0  # 共鸣解放可用性检查的最长等待上限。
    # In the reference capture Z runs from 00:00:42:02 to 00:00:43:10
    # (about 1.33s).  The previous 2.32s frame-data value delayed R too much.
    AXIS_HEAVY_DURATION = 1.33  # phase 7/14：强化重击 Z 的默认动作窗口。

    # 处决（F）位置来自作者录像复核：phase 7 插在 `a 闪 A e A` 之后、
    # phase 14 插在 `a 闪 A` 之后；循环第一轮不打，第二、三轮才打。
    # 提示检测直读 f_break_full 模板，不复用 task.check_f_break()，
    # 因为它的 can_break 标志是粘的、只有框架自己的 f_break() 会清。
    AXIS_F_BREAK_ENABLED = True  # 总开关：False 时轴内一个 F 都不发。
    AXIS_F_BREAK_FROM_ROUND = 1  # 循环轮门槛：1 = 从第二轮开始打（作者录像）。
    AXIS_F_BREAK_THRESHOLD = 0.92  # 处决提示模板阈值，与框架 check_f_break 一致。
    AXIS_F_BREAK_PROBE = 0.35  # 探处决提示的窗口；探不到就直接走下一格。
    AXIS_F_BREAK_PROBE_INTERVAL = 0.08  # 探测时的读屏间隔。
    AXIS_F_BREAK_BURST = 0.60  # 连发 F、等处决演出开始的上限。
    AXIS_F_BREAK_INTERVAL = 0.15  # 连发 F 的间隔，演出里的按键会被丢掉。
    AXIS_F_BREAK_ANIM_TIMEOUT = 5.0  # 处决演出的等待上限。
    AXIS_F_BREAK_HUD_SETTLE = 0.35  # 队伍 HUD 连续回来这么久算演出结束。
    AXIS_F_BREAK_HUD_INTERVAL = 0.02  # 等演出时的读帧间隔。

    # 专属轴的精确队伍门槛和 phase 执行角色映射。
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
        # phase: (下一 phase, 下一角色, 是否消耗变奏入场)
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
        # 仅精确匹配弗卜维三人队，其他队伍继续走默认弗洛洛逻辑。
        chars = getattr(self.task, 'chars', ()) if self.task is not None else ()
        names = {getattr(char, 'char_name', None) for char in chars if char is not None}
        return names == self._AXIS_TEAM

    def _axis_state(self):
        # 共享 task 状态：phase/step 控制进度，target 控制切人，
        # phase_started 和 step_wait_started 防止重复入场或无限重试。
        state = getattr(self.task, '_dpv_axis_state', None)
        if not isinstance(state, dict) or state.get('team') != self._AXIS_TEAM:
            state = {
                'team': set(self._AXIS_TEAM),
                'phase': 0,
                'target': 'char_douling',
                'step': 0,
                'phase_started': False,
                'step_wait_started': None,
                'cycle_round': 0,
            }
            self.task._dpv_axis_state = state
        else:
            state.setdefault('step', 0)
            state.setdefault('phase_started', False)
            state.setdefault('step_wait_started', None)
            state.setdefault('cycle_round', 0)
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
        # 通过槽位切换并轮询确认，绕开战斗目标 HUD 暂时消失造成的切人阻塞。
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
        if phase == 14:
            # 跑完一轮循环记一次；phase 14 的处决靠它区分第一轮和后续轮。
            state['cycle_round'] = state.get('cycle_round', 0) + 1
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
        # 阶段动作按持久化游标执行；失败动作保留在原 step 等待下一次循环重试。
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

    def _axis_normal(self, count=1, interval=None, cast_times=None):
        # 根据当前 A1/A2/A3 计数发送普通攻击，并使用对应派生时间保护动作边界。
        if interval is None:
            interval = self.AXIS_NORMAL_INTERVAL
        for _ in range(count):
            started_at = time.perf_counter()
            self.click()
            self.task.next_frame()
            if cast_times is None:
                cast_times = self.AXIS_NORMAL_CAST_TIMES
            cast_time = cast_times[self._axis_attack_index % len(cast_times)]
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

    def _axis_dodge_enhanced(self, cast_time=None):
        # 闪避期间预输入强化 A；普通链和 3A 链使用不同的动作窗口。
        """Dodge and queue enhanced A before the dodge animation ends."""
        if cast_time is None:
            cast_time = self.AXIS_DODGE_ENHANCED_CAST_TIME
        started_at = time.perf_counter()
        self.sleep(self.AXIS_DODGE_PRE_SLEEP)
        self.task.next_frame()
        self.task.click(key='right')
        self.sleep(self.AXIS_DODGE_ENHANCED_DELAY)
        self.click()
        self.task.next_frame()
        self._axis_wait_cast(started_at, cast_time)
        self._axis_attack_index = 0
        return True

    def _axis_enhanced_followup(self):
        """Queue the next enhanced A with the short post-chain window."""
        started_at = time.perf_counter()
        self.click()
        self.task.next_frame()
        self._axis_wait_cast(started_at, self.AXIS_DODGE_ENHANCED_CAST_TIME)
        self._axis_attack_index = 0
        return True

    def _axis_three_normal_dodge(self):
        self._axis_normal(3)
        self._axis_dodge_enhanced(self.AXIS_CHAIN_DODGE_ENHANCED_CAST_TIME)
        self._axis_dodge()
        return True

    def _axis_phase7_three_normal(self):
        # phase 7/14：在固定总窗口内按间隔连续发送三次平 A。
        started_at = time.perf_counter()
        while time.perf_counter() - started_at < self.AXIS_PHASE7_THREE_A_DURATION:
            self.click()
            self.task.next_frame()
            self.sleep(self.AXIS_PHASE7_THREE_A_INTERVAL, check_combat=False)
        return True

    def _axis_phase7_three_normal_dodge(self):
        self._axis_phase7_three_normal()
        self._axis_dodge_enhanced(self.AXIS_CHAIN_DODGE_ENHANCED_CAST_TIME)
        self._axis_dodge()
        return True

    def _axis_phase7_enhanced(self):
        started_at = time.perf_counter()
        self.click()
        self.task.next_frame()
        self._axis_wait_cast(started_at, self.AXIS_PHASE7_Q_TO_A_CAST_TIME)
        self._axis_attack_index = 0
        return True

    def _axis_phase7_liberation(self):
        # phase 7：R 动画期间不能提前切人，等待 HUD 恢复后再进入 phase 8。
        self.sleep(self.AXIS_PHASE7_Z_TO_R_DELAY, check_combat=False)
        started_at = time.perf_counter()
        self.send_liberation_key()
        self.record_liberation_use()
        self.task.next_frame()
        self._axis_wait_cast(started_at, self.AXIS_LIBERATION_CAST_TIME)
        return True

    def _axis_f_break_prompt(self):
        """读一帧处决提示模板；读不到就当没有提示。"""
        try:
            return bool(self.task.find_one('f_break_full',
                                           threshold=self.AXIS_F_BREAK_THRESHOLD))
        except Exception:
            # 读屏失败按"没有提示"处理：顶多退回没有处决的那套流程。
            return False

    def _axis_wait_f_break_end(self):
        """等处决演出结束：队伍 HUD 消失期间不跑战斗检查。"""
        started_at = time.perf_counter()
        back_since = None
        while time.perf_counter() - started_at < self.AXIS_F_BREAK_ANIM_TIMEOUT:
            self.task.next_frame()
            if not self.task.in_team()[0]:
                back_since = None
            elif back_since is None:
                back_since = time.perf_counter()
            elif time.perf_counter() - back_since >= self.AXIS_F_BREAK_HUD_SETTLE:
                self.logger.info(
                    f'dpv axis f_break done {time.perf_counter() - started_at:.2f}s')
                return True
            self.sleep(self.AXIS_F_BREAK_HUD_INTERVAL, check_combat=False)
        self.logger.warning('dpv axis f_break animation wait timed out')
        return True

    def _axis_f_break(self):
        """在 phase 表指定的位置打处决。

        先短窗口探提示：没有提示就直接进下一格，不占动作窗口。探到提示才连发 F，
        并等演出演完、队伍 HUD 稳定回来再继续；处决演出带全局时停，不等会把
        后面每一格的时长整体推歪。
        """
        if not self.AXIS_F_BREAK_ENABLED:
            return True
        seen = self._axis_f_break_prompt()
        deadline = time.perf_counter() + self.AXIS_F_BREAK_PROBE
        while not seen and time.perf_counter() < deadline:
            self.task.next_frame()
            self.sleep(self.AXIS_F_BREAK_PROBE_INTERVAL, check_combat=False)
            seen = self._axis_f_break_prompt()
        if not seen:
            self.logger.info('dpv axis f_break skipped: no execution prompt')
            return True
        started_at = time.perf_counter()
        broke = False
        while time.perf_counter() - started_at < self.AXIS_F_BREAK_BURST:
            self.task.send_key('f', after_sleep=0)
            # 自己发 F，框架的 can_break 不会被 f_break() 清，这里手动复位。
            self.task.can_break = False
            self.task.next_frame()
            if not self.task.in_team()[0]:
                broke = True
                break
            self.sleep(self.AXIS_F_BREAK_INTERVAL, check_combat=False)
        if not broke:
            self.logger.warning('dpv axis f_break: prompt seen but no execution started')
            return True
        self._axis_wait_f_break_end()
        # 处决动画结束后普通攻击链从头开始。
        self._axis_attack_index = 0
        return True

    def _axis_cycle_f_break(self):
        """phase 14 的处决：作者录像里第一轮循环不打，从第二轮开始打。"""
        if not self.AXIS_F_BREAK_ENABLED:
            return True
        state = self._axis_state()
        if state.get('cycle_round', 0) < self.AXIS_F_BREAK_FROM_ROUND:
            self.logger.info('dpv axis f_break skipped: first loop round')
            return True
        return self._axis_f_break()

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

    def _axis_echo(self, post_sleep=None):
        if not self.echo_available():
            return False
        started_at = time.perf_counter()
        clicked = self.click_echo(time_out=0)
        if clicked:
            self.task.next_frame()
            self._axis_wait_cast(started_at, self.AXIS_ECHO_CAST_TIME)
            if post_sleep is None:
                post_sleep = self.AXIS_ECHO_POST_SLEEP
            self.sleep(post_sleep, check_combat=False)
        return clicked

    def _axis_echo_queue_next(self):
        """Use echo as a hand-off and queue the next A during its animation."""
        if not self.echo_available():
            return False
        clicked = self.click_echo(time_out=0)
        if clicked:
            self.task.next_frame()
            self.sleep(0.04, check_combat=False)
        return clicked

    def _axis_phase2_echo_queue_next(self):
        # phase 2：释放 R 后等待实机观察到的窗口，让下一发强化 A 能接上。
        """Queue phase-2 A after the observed Q animation settle window."""
        if not self.echo_available():
            return False
        clicked = self.click_echo(time_out=0)
        if clicked:
            self.task.next_frame()
            self.sleep(self.AXIS_PHASE2_Q_TO_A_DELAY, check_combat=False)
        return clicked

    def _axis_phase2_enhanced(self):
        # phase 2：发送一发强化 A；强化攻击结束后重置普通攻击计数到 A1。
        started_at = time.perf_counter()
        self.click()
        self.task.next_frame()
        self._axis_wait_cast(started_at, self.AXIS_PHASE2_ENHANCED_CAST_TIME)
        self._axis_attack_index = 0
        return True

    def _axis_phase2_heavy(self):
        # phase 2：使用 phase 2 专用短 Z 窗口，输入完成后交给切人衔接。
        return self._axis_heavy(self.AXIS_PHASE2_HEAVY_DURATION)

    def _do_axis_perform(self):
        # 专属轴入口：按 phase 路由角色，并执行该 phase 的固定动作序列。
        self.last_liberation = -1
        # 处决位置由 phase 表决定，关掉框架切人时的自动 F，免得插一发。
        self.check_f_on_switch = False
        phase = self._axis_sync_phase()
        if self._axis_route_to_actor(phase):
            return
        self._axis_start_phase()
        if phase == 2:  # phase 2 启动：AA -> 声骸 -> 强化 A -> E -> 强化 A -> Z。
            actions = (
                lambda: self._axis_normal(2), self._axis_phase2_echo_queue_next,
                self._axis_phase2_enhanced, self._axis_resonance,
                self._axis_phase2_enhanced, self._axis_phase2_heavy,
            )
        elif phase == 4:  # phase 4 启动：A -> 闪 -> 强化 A -> 共鸣解放。
            actions = (self._axis_normal, self._axis_dodge_enhanced,
                       self._axis_liberation)
        elif phase == 7:  # phase 7 启动：A 闪 A -> E A -> 处决 F -> 3A 闪避链 -> 声骸 -> 强化 A -> Z -> R。
            actions = (
                self._axis_normal, self._axis_dodge_enhanced,
                self._axis_resonance, self._axis_enhanced_followup,
                self._axis_f_break,
                self._axis_dodge,
                self._axis_phase7_three_normal_dodge, self._axis_phase7_three_normal_dodge,
                self._axis_phase7_three_normal_dodge,
                self._axis_phase7_three_normal,
                lambda: self._axis_echo(self.AXIS_PHASE7_ECHO_POST_SLEEP), self._axis_phase7_enhanced,
                self._axis_heavy, self._axis_phase7_liberation,
            )
        elif phase == 12:  # phase 12 循环：A -> 闪 -> 强化 A -> E -> 强化 A。
            actions = (self._axis_normal, self._axis_dodge_enhanced,
                       self._axis_resonance, self._axis_enhanced_followup)
        elif phase == 14:  # phase 14 循环：A 闪 A -> 处决 F（第二轮起）-> 3A 闪避链 -> 声骸 -> 强化 A -> E -> 强化 A -> Z -> R。
            actions = (
                self._axis_normal, self._axis_dodge_enhanced,
                self._axis_cycle_f_break,
                self._axis_phase7_three_normal_dodge, self._axis_phase7_three_normal_dodge,
                self._axis_phase7_three_normal,
                lambda: self._axis_echo(self.AXIS_PHASE7_ECHO_POST_SLEEP),
                self._axis_phase7_enhanced, self._axis_resonance,
                 self._axis_enhanced, self._axis_heavy, self._axis_phase7_liberation,
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
