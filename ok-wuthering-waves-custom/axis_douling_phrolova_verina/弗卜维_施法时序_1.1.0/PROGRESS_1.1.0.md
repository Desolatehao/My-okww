# DPV 轴 1.1.0 进展

## 版本范围

1.1.0 基于 1.0.8 当前快照封版，保留已验证参数和当前四链维里奈 phase 路由。未修改通用框架，也未调整其它无关 phase。

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
```

## 验证

- 三个角色脚本执行 Python 语法检查。
- 版本 ZIP 排除 `__pycache__`。
- 通用 `src/char` 未修改。
