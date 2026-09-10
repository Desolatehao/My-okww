import time

from src.char.BaseChar import SwitchPriority
from src.char.Cantarella import Cantarella as NativeCantarella


class Cantarella(NativeCantarella):
    """弗坎莫队(弗洛洛/坎特蕾拉/莫宁)里的坎特蕾拉。非本队时整套走原版。

    【她不驱动任何一段轴】: 启动轴由莫宁起跑, 循环轴由弗洛洛起跑, 中间她上场一次
    是宏按数字键(变奏)切进来的。所以框架调到她的 do_perform 就说明宏散了
    (切人失败 / 脱战重进) —— 打一小段普攻把场子交出去, 让弗洛洛重新拿到入口。

    【原版的 is_forte_full() 一行没动】: 宏要读她的回路时用的就是那个函数,
    上游以后改了它, 这条轴自动跟着走。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 【自定义 __init__ 里跟内置版取值不同的字段会被 CharFactory 打回内置值】
        # (apply_team_char_classes 里 replacement.__dict__.update(char.__dict__))。
        # 这里新加的字段内置版没有, 不受影响
        self.macro_yield_logged = 0.0

    @property
    def is_healer(self):
        """【本队里不把坎特蕾拉算作奶妈】。

        CharFactory 把她登记成 CharType.HEALER, 而 AutoCombatTask.run() 每一轮的
        【第一件事】就是 switch_healer() —— 它排在任何角色的 do_perform 之前,
        看到"当前角色不是奶妈、队里有奶妈"就直接切过去。
        这条轴的循环入口是弗洛洛(主C), 不关掉的话每一圈开头都要白花两次切人。

        【本队两个奶都要关】: 莫宁那边同理, 见 Mornye.is_healer。只关一个没用 ——
        has_healer 是"队里还有没有奶妈", 剩一个照样成立。
        【只在本队关掉】, 非本队保持原样, 不影响别的配队。
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
            if char is not None and char.name in {'Phrolova', 'Mornye'}:
                team_members += 1
        return team_members == 2

    def macro(self):
        """拿到持宏的弗洛洛实例。【按能力找, 不按名字找】。"""
        for char in self.task.chars:
            if char is None or char is self:
                continue
            if hasattr(char, 'perform_loop') and hasattr(char, 'quick_switch'):
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
            return super().do_perform()
        now = time.time()
        if now - self.macro_yield_logged > 5:
            self.macro_yield_logged = now
            self.logger.info('cantarella: macro drives this team, handing the field back')
        # 【不要在这里跑循环轴】: 循环轴的第一步假设弗洛洛刚变奏入场, 从坎特蕾拉
        # 这里起跑一定错位。打一小段把场子交出去就行
        self.continues_normal_attack(0.6)
        return self.switch_next_char()

    def get_switch_priority(self, current_char=None, has_intro=False, target_low_con=False):
        """启动轴待跑时让位给莫宁(轴的第一个动作是她的 E)。

        【这里别打日志】: 框架会对每个候选反复调用, 会刷屏。
        """
        if self.is_in_phro_cycle:
            macro = self.macro()
            if macro is not None and macro.opener_pending():
                return SwitchPriority.NO
        return super().get_switch_priority(current_char, has_intro, target_low_con)
