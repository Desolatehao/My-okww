# DPV 轴 1.2.0 进展

## 版本范围

1.2.0 基于 1.1.1 当前快照封版，保留已验证参数和当前四链维里奈 phase 路由。未修改通用框架，也未调整其它无关 phase。

## 已验证修正

### phase 2：弗洛洛 `aa q A e A z`

- Q 后首个强化 A 等待：`0.90 s`。
- 两次强化 A 动作窗口：`0.55 s`。
- Z 输入保持窗口：`0.30 s`。
- 已确认第二次强化 A 和 Z 均可释放后再切换卜灵。

### phase 5：卜灵 `aa` 后 Q

- 平 A 总窗口恢复为 `0.70 s`，窗口内输入间隔保持 `0.15 s`。
- phase5 声骸 Q 使用独立 `0.05 s` 按键保持时长，避免延长平 A 窗口代替 Q 输入。
- 该组合用于完成目标 `aa q` 后进入 phase 6。

### phase 7：弗洛洛长连段

- 每段 `3a` 持续输入窗口保持 `1.70 s`。
- phase 7 窗口内平 A 输入间隔：`0.10 s`，用于保证三次 A 在闪避前有效进入队列。
- 已确认第三次平 A 能触发强化 A 图标，再由闪避打断并释放强化 A。
- 尾段 Q 后强化 A 等待：`0.10 s`。
- phase 7 声骸后额外衔接等待：`1.00 s`（不再沿用全局 `2.00 s`）。
- 尾段 Z 后 R 延迟：`1.75 s`；`1.60 s` 实战有偶发未释放 R 就切人的情况，`1.75 s` 作为当前稳定值。
- phase 7 R 发送后等待 `3.30 s` 动画/HUD 恢复，再切入 phase 8 维里奈，避免在 R 动画期间提前切人造成 phase8/phase9 路由错位。
- phase 8 维里奈从切入时刻开始计算 `1.00 s` 总窗口，窗口内先执行一次 A，再进入 phase 9 卜灵。
- phase 9 改为直接复用 phase 3 的动作表 `E -> 4A -> 跳 -> 空中 A -> Z -> Z`，实测输入表现为 `E -> A -> 跳 -> 空中 A -> Z -> Z`。
- phase 9 双 Z 使用 `0.75 s` 单次窗口和 `0.20 s` 间隔；第二个 Z 后不等待 `0.35 s`，直接切人取消后摇，等效于 phase 3 用 R 快速取消后摇。

### 维里奈四链 phase

- phase 6 恢复维里奈 R，动作顺序为 `E -> Q -> 闪 -> R -> 跳 -> AA`。
- phase 13 保持循环阶段跳过维里奈 R，动作顺序为 `跳 -> AA`。
- 这是四链配置的专用路由，不改变通用框架或其他角色的 R 动作。

### phase 11：卜灵 `AA -> Q -> R`

- 第二次 A 后增加 `0.15 s` 专用等待，确保【卦象·艮】登记后再释放 Q。

### phase 14：弗洛洛循环长连段

- 修正两段带闪避的 `3a` 及末段 `3a` 的输入 helper，统一复用 phase 7 的 `1.70 s` 总留场窗口和 `0.10 s` 普通 A 输入间隔。
- 原通用 `A1/A2/A3` 派生等待（`0.67/0.60/0.53 s`）会使第三次 A 偶发未进入队列，导致闪避后没有强化 A；本次仅调整 phase14 调用，不改变动作顺序、延奏衔接或其他 phase。
- 修正 phase14 尾段衔接：Q 后等待从全局 `2.00 s` 改为 phase7 同值 `1.00 s`，Q 后第一发强化 A 从通用 `1.33 s` 改为 phase7 短窗口 `0.10 s`，随后保持 `E -> 强化 A -> Z -> R`。
- phase14 末尾 Z -> R 改为复用 phase7 专用 helper，沿用 `1.75 s` 的 Z 后等待后再发 R。

## 处决 F 接入（2026-09-13 修改，待实机复测）

### 来源

作者录像复核：启动轴 `弗 a 闪 A e A` 之后插了一次处决 F，然后才 `闪 3a ...`；
循环轴第一轮没有处决（旧 Boss 已被打死、新 Boss 还没削韧），
第二、三轮都在 `弗 a 闪 A` 之后插处决 F，再继续 `3a 闪 ...`。

### 改动

- phase 7：在 `_axis_enhanced_followup`（`e A` 那一格）之后、`闪` 之前插入 `_axis_f_break`。
- phase 14：在 `_axis_dodge_enhanced`（`a 闪 A` 那一格）之后插入 `_axis_cycle_f_break`；
  共享状态新增 `cycle_round`，每跑完一轮循环 +1，`AXIS_F_BREAK_FROM_ROUND = 1` 时第一轮跳过、第二轮起才打。
- 两个位置都先探提示再按键：探到才连发 F，探不到就直接进下一格，不占动作窗口。
- `_do_axis_perform` 里把 `check_f_on_switch` 置 False，避免框架在切人时另外插一发自动 F。

### 判据与等待

- 提示判据直读 `f_break_full` 模板，阈值 `0.92`（与框架 `check_f_break` 一致）。
  不复用 `task.check_f_break()`：它的 `can_break` 是粘的，只有框架自己的 `f_break()` 会清，
  自己发 F 时清不掉，拿它当判据会一直读到"有提示"。
- 探测窗口 `0.35 s`（间隔 `0.08 s`）；探到后连发 F 的上限 `0.60 s`（间隔 `0.15 s`）。
- 用 `in_team()` 掉下去判断处决演出已经开始，随后等队伍 HUD 连续回来 `0.35 s` 才算演完
  （上限 `5.0 s`）。处决演出带全局时停，不等会把后面每一格的时长整体推歪。
- 整个等待过程一律 `check_combat=False`，避免 HUD 消失被判成脱战。

### 待复测

- 处决演出时长随怪物/角色不同（参考包实测 0.5–5 s），`AXIS_F_BREAK_ANIM_TIMEOUT = 5.0` 是否够。
- 第二轮门槛是否与实机一致：本改动按录像做成"第一轮不打"，如果实机第一轮就有提示，可以改判据。
- 处决后接 `闪 3a ...` 的衔接时序（处决结束时攻击链已重置，代码把 `_axis_attack_index` 归零）。

## 当前关键参数

```python
# Phrolova.py
AXIS_PHASE2_Q_TO_A_DELAY = 0.90
AXIS_PHASE2_ENHANCED_CAST_TIME = 0.55
AXIS_PHASE2_HEAVY_DURATION = 0.3
AXIS_PHASE7_THREE_A_DURATION = 1.70
AXIS_PHASE7_THREE_A_INTERVAL = 0.10
AXIS_PHASE7_ECHO_POST_SLEEP = 1.00
AXIS_PHASE7_Q_TO_A_CAST_TIME = 0.10
AXIS_PHASE7_Z_TO_R_DELAY = 1.75

# Verina.py
AXIS_PHASE8_SWITCH_DELAY = 1.00

# Douling.py
AXIS_PHASE9_HEAVY_DURATION = 0.75
AXIS_PHASE9_HEAVY_GAP = 0.20
AXIS_PHASE9_JUMP_TO_A_DELAY = 0.20
AXIS_PHASE9_AERIAL_INTERVAL = 0.10
AXIS_PHASE9_AERIAL_CAST_TIME = 0.10
AXIS_PHASE9_AERIAL_POST_SLEEP = 0.20
AXIS_PHASE9_AERIAL_READY_TIMEOUT = 0.50

# Douling.py
AXIS_PHASE5_AA_DURATION = 0.70
AXIS_PHASE5_AA_INTERVAL = 0.15
AXIS_PHASE5_ECHO_DOWN_TIME = 0.05

# Phrolova.py（处决 F，1.2.0 新增，待实机复测）
AXIS_F_BREAK_ENABLED = True
AXIS_F_BREAK_FROM_ROUND = 1      # 1 = 循环第一轮不打，第二轮起打
AXIS_F_BREAK_THRESHOLD = 0.92
AXIS_F_BREAK_PROBE = 0.35
AXIS_F_BREAK_PROBE_INTERVAL = 0.08
AXIS_F_BREAK_BURST = 0.60
AXIS_F_BREAK_INTERVAL = 0.15
AXIS_F_BREAK_ANIM_TIMEOUT = 5.0
AXIS_F_BREAK_HUD_SETTLE = 0.35
```

## 验证

- 三个角色脚本执行 Python 语法检查。
- 处决 F 分支用桩任务跑过四种场景：无提示（不按键）、提示后触发（等演出结束）、
  提示但未触发（走满 `0.60 s` 上限后继续）、循环第一轮（跳过探测）。
- 版本 ZIP 排除 `__pycache__`。
- 通用 `src/char` 未修改。
