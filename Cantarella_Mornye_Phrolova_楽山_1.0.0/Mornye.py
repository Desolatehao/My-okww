import time

from src.char.BaseChar import SwitchPriority
from src.char.Mornye import Mornye as NativeMornye


class Mornye(NativeMornye):
    """弗坎莫队(弗洛洛/坎特蕾拉/莫宁)里的莫宁。非本队时整套走原版。

    【她是启动轴的入口】: 轴的第一个动作是她的 E(回血 + 让治疗套的攻击加成挂上),
    所以启动轴待跑时她返回 MUST, 由她的 do_perform 把宏拉起来。

    宏体在同目录的 Phrolova.py 里 —— 自定义角色文件由 CustomCharLoader 按路径单独
    加载, 互相 import 不到, 但同一个 task 下用 task.chars 拿得到彼此的实例,
    这是跨文件复用宏原语的唯一路子。

    【循环轴不由她驱动】(那一段的入口是弗洛洛), 所以启动轴跑过之后她走到 do_perform
    就说明宏散了 —— 打一小段把场子交出去, 让弗洛洛重新拿到入口。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 【自定义 __init__ 里跟内置版取值不同的字段会被 CharFactory 打回内置值】
        # (apply_team_char_classes 里 replacement.__dict__.update(char.__dict__))。
        # 这里新加的字段内置版没有, 不受影响
        self.macro_yield_logged = 0.0

    @property
    def is_healer(self):
        """【本队里不把莫宁算作奶妈】。

        CharFactory 把她登记成 CharType.HEALER —— 原版她确实兼职奶。
        但 AutoCombatTask.run() 在战斗循环的【第一件事】就是 switch_healer(),
        排在任何角色的 do_perform 之前; 它看到"当前角色不是奶妈、队里有奶妈"就
        直接切过去。而【这条轴的循环入口是弗洛洛(主C)】—— 于是每一圈开头都要白花
        "切莫宁 -> 再切回弗洛洛"两次切人(约 1.8 秒), 而且弗洛洛被切下去还带着换人 CD。

        这条轴不需要那个保护: 莫宁本来就在轴上大量出场(每一圈都有她一整段),
        开局第一个动作还就是她的回血 E。
        【只在本队关掉】, 非本队保持原样, 不影响别的配队。
        等价的用户侧开关是任务配置里的 "Switch to Healer before and after Combat",
        但那个是全局的, 会连别的队一起关掉。

        (清达莫 / 爱琳莫两队定位过同一个问题, 处理方式相同。)
        """
        try:
            if self.is_in_phro_cycle:
                return False
        except Exception:
            pass  # __init__ 里 check_f_on_switch 会先读一次, 那时队伍还没加载
        return super().is_healer

    @property
    def is_in_phro_cycle(self) -> bool:
        team_members = 0
        for char in self.task.chars:
            if char is not None and char.name in {'Phrolova', 'Cantarella'}:
                team_members += 1
        return team_members == 2

    def macro(self):
        """拿到持宏的弗洛洛实例。【按能力找, 不按名字找】—— 她那份自定义没启用时
        这里返回 None, 老老实实走原版轮换, 而不是拿着一个没有 perform_opener 的实例崩掉。
        """
        for char in self.task.chars:
            if char is None or char is self:
                continue
            if hasattr(char, 'perform_opener') and hasattr(char, 'quick_switch'):
                return char
        return None

    def do_perform(self):
        if not self.is_in_phro_cycle:
            return super().do_perform()
        # 处决全程由宏自己按 —— 留着框架的自动 F 会在切人时插一发, 而击破动画带
        # 全局时停 + 队伍 HUD 消失, 正好把切人循环判成脱战
        self.check_f_on_switch = False
        macro = self.macro()
        if macro is None:
            self.logger.warning('phro cycle: Phrolova custom code is off, '
                                'falling back to the native rotation')
            return super().do_perform()

        blocked = macro.opener_blocked_by()
        if blocked is None:
            # 【标记要在跑之前落】: perform_opener 中途抛异常(脱战/任务被停)也不能
            # 让启动轴重跑 —— reset_state 会把 armed 重新置回来
            macro.opener_armed = False
            macro.last_opener = time.time()
            # 【把自己传进去】: 框架是因为莫宁在场才调的这个 do_perform, 所以这就是
            # "现在场上是谁"最可靠的答案。
            # 【不能让它去读屏判断】: in_team() 在战斗开局的头 0.8 秒会说谎
            # (队伍 HUD 还在渐入, 三个槽位的文本不是同时出现的)
            if macro.perform_opener(self):
                return
            self.logger.warning('phro opener aborted, falling back to the native rotation')
            return super().do_perform()

        # 启动轴跑过了: 循环轴由弗洛洛驱动。走到这里说明宏散了(切人失败/脱战重进),
        # 打一小段把场子交给她重新起跑。
        # 【不要在这里跑循环轴】: 循环轴的第一步假设弗洛洛刚变奏入场, 从莫宁这里
        # 起跑一定错位
        now = time.time()
        if now - self.macro_yield_logged > 5:
            self.macro_yield_logged = now
            self.logger.info(f'mornye: opener not pending ({blocked}), handing the field back')
        self.continues_normal_attack(0.6)
        return self.switch_next_char()

    def get_switch_priority(self, current_char=None, has_intro=False, target_low_con=False):
        """启动轴待跑时莫宁【必须】先上场 —— 轴的第一个动作是她的 E。

        【至少要留一个 MUST 候选】: 全队都是 NO 的话框架只会打一下普攻原地打转。
        本队里弗洛洛和坎特蕾拉在启动轴待跑时都返回 NO, 所以这个 MUST 是必需的。

        【这里别打日志】: 框架会对每个候选反复调用, 会刷屏。
        """
        if self.is_in_phro_cycle:
            macro = self.macro()
            if macro is not None and macro.opener_pending():
                return SwitchPriority.MUST
        return super().get_switch_priority(current_char, has_intro, target_low_con)
