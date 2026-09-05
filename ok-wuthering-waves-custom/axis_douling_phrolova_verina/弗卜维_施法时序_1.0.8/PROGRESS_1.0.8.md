# DPV 轴 1.0.8 进展

## 版本范围

1.0.8 基于 1.0.7 的连续实机调试结果，整理 phase 2、phase 5 和 phase 7 的已验证参数。未修改通用框架，也未调整其它无关 phase。

## 已验证修正

### phase 2：弗洛洛 `aa q A e A z`

- Q 后首个强化 A 等待：`0.90 s`。
- 两次强化 A 动作窗口：`0.55 s`。
- Z 输入保持窗口：`0.30 s`。
- 已确认第二次强化 A 和 Z 均可释放后再切换卜灵。

### phase 5：卜灵 `aa` 后 Q

- 作者视频切入到 Q 为 `18.728 -> 20.728`；本次实测为 `21.940 -> 25.402`，且疑似多完成第三次 A。
- A 总窗口调整为 `0.60 s`，窗口内输入间隔调整为 `0.30 s`。
- 目标是变奏入场后稳定执行两次 A，再释放 Q 并进入 phase 6。

### phase 7：弗洛洛长连段

- 每段 `3a` 改为持续输入窗口：`1.70 s`。
- 窗口内平 A 输入间隔：`0.15 s`。
- 已确认第三次平 A 能触发强化 A 图标，再由闪避打断并释放强化 A。
- 尾段 Q 后强化 A 等待：`0.10 s`。
- 尾段 Z 后 R 延迟：`1.60 s`；此前 `0.30 s` 无法触发 R，`1.60 s` 已实机确认可用。

## 当前关键参数

```python
# Phrolova.py
AXIS_PHASE2_Q_TO_A_DELAY = 0.90
AXIS_PHASE2_ENHANCED_CAST_TIME = 0.55
AXIS_PHASE2_HEAVY_DURATION = 0.3
AXIS_PHASE7_THREE_A_DURATION = 1.70
AXIS_PHASE7_THREE_A_INTERVAL = 0.15
AXIS_PHASE7_Q_TO_A_CAST_TIME = 0.10
AXIS_PHASE7_Z_TO_R_DELAY = 1.60

# Douling.py
AXIS_PHASE5_AA_DURATION = 0.60
AXIS_PHASE5_AA_INTERVAL = 0.30
```

## 验证

- 三个角色脚本执行 Python 语法检查。
- 版本 ZIP 排除 `__pycache__`。
- 通用 `src/char` 未修改。
