# OKWW 机制笔记

跨轴通用的框架机制。开新轴之前先过一遍，能省掉大量"为什么它不动"的排查。

**来源与可信度**

| 来源 | 说明 |
| --- | --- |
| 上游 `ok-wuthering-waves` 的 `src/char/BaseChar.py` | 2026-09-10 从 master 抓取。**会随上游变化，用之前最好重新核对一遍** |
| 本仓库弗卜维轴的代码与笔记 | 1.2.0 版本实测过的结论 |
| 第三方的参考轴包 | 见 `参考资料/弗卜维涉及资料/`，作者各自的环境和习惯不同 |

标 ⚠️ 的是推断或未经实机验证的内容。

---

## 0. 先确认这些，不然白忙

- **键位映射**要和游戏一致：共鸣技能 / 共鸣解放 / 声骸 / 闪避 / 跳跃。
  注意 Q 和 R 是**约定叫法**，不一定是物理按键。弗卜维轴的约定是 `Q = 声骸`、`R = 解放`，
  反过来会让某个 phase 卡在等技能上。
- **`Use Liberation` 必须开**，否则 `click_liberation()` 直接返回 False。
- **`Check Levitator` 必须开**，否则 `flying()` 永远返回 False，所有跳A / 空中判定失效。
- 三名角色都要装备主声骸；声骸是轴里的固定动作。

---

## 1. 切人

### 1.1 两条切人路径

| 方式 | 行为 | 什么时候用 |
| --- | --- | --- |
| `switch_next_char()` | 框架选人：先 `is_forte_full()`、清 `has_intro`、记录 `_liberation_available`、处理探索工具箱，然后由 task 按角色定位 / 优先级 / 延奏挑目标 | 普通轮转 |
| 槽位直切 | 直接 `task.send_key(slot)`，用 `task.in_team()` 确认当前 index，自己做状态簿记 | 需要精确控制切谁时 |

弗卜维轴全程用槽位直切，原因见 1.4。

### 1.2 槽位直切必须做的簿记

缺任何一项都会让框架状态和游戏不同步：

```python
self.task.in_liberation = False
source.switch_out(con_full=free_intro)
target.is_current_char = True
target.has_intro = free_intro
target.has_sub_dps_intro = free_intro and source.is_sub_dps
target.last_switch_in_time = time.time()
if free_intro:
    self.task.add_freeze_duration(now, target.intro_motion_freeze_duration, -100)
    source.last_outro_time = now
```

⚠️ **顺序很重要**：必须在 `in_team()` 确认当前 index 已经变成目标之后，才更新
`is_current_char` / `has_intro`。提前改会让框架以为已经切过去了，比多等一会儿糟糕得多。

### 1.3 切换优先级 `SwitchPriority`

```
NO = 0  <  LOW = 100  <  NORMAL = 200  <  HIGH = 300  <  MUST = 400
```

取最高者。数值之间留了 100 的间隔，可以返回 `SwitchPriority.HIGH + 1` 这种微调值。

- 默认实现：`healer_full_con_switch_locked()` 为真 → `NO`，否则 `NORMAL`。
- 本轴用法：轴启用时，**下一个目标返回 `MUST`，其余队员返回 `NO`**，从而独占切人权。

### 1.4 切人相关的两个坑

- **目标 HUD 会在解放/声骸动画期间消失**。此时 `switch_next_char()` 的目标选择会报
  `target lost`，表现为"卡住好几秒"。这就是本轴改用槽位直切的原因。
- **治疗者满协奏切人锁 = 16 秒**（`HEALER_FULL_CON_SWITCH_LOCKOUT`）。
  治疗者满协奏下场后，默认 16 秒内不能再被切回来。卜灵 ↔ 维里奈之间有短切，
  所以本轴在 `healer_full_con_switch_locked()` 里直接返回 `False` 把它关掉。

### 1.5 切人 CD

- `wait_switch_cd()`：距上次 `last_perform` 不足 1 秒就先普攻补时间。
- 参考轴的常见写法是 `time_elapsed_accounting_for_freeze(last_perform) < 8 → NO`，
  即"出场 8 秒内不让别人切走"。⚠️ 这个 8 秒是参考实现的**选择**，不是框架硬限制。

### 1.6 切人之后会自动平A（重点）

这是很容易被忽略、但会直接毁掉连段计数的一条：

- **变奏入场（`has_intro=True`）的入场动作本身就是一次攻击**，而且会顶掉普攻连段计数。
  弗洛洛实测：变奏入场复用 A2，所以下一个显式 `a` 是 **A3（0.53s）**；手动切入则从 A1 开始。
  代码里就体现为 `self._axis_attack_index = 2 if self.has_intro else 0`。
- `wait_down()` 在"没有控物且刚入场"时，也会用 `continues_normal_attack(intro_motion_freeze_duration)`
  边下落边打。
- `intro_motion_freeze_duration` 默认 **0.9s**，是入场动作的冻结时长。

**所以在轴里：**

- 入场后要留一个"禁止过早输入"的安全窗口。本轴用 `AXIS_INTRO_LOCK`
  （卜灵 `0.90` / 弗洛洛 `1.30` / 维里奈 `0.90`）。
- 等待入场时用 `wait_intro(time_out=..., click=False)`，**不要注入计划外普攻**，
  让 phase 表独占所有攻击输入。
- 连段计数要按"这次是不是变奏入场"分别处理，不能一律从第一段算起。

---

## 2. CD 与技能可用性

### 2.1 判定

| 方法 | 说明 |
| --- | --- |
| `has_cd(box_name)` | 该技能 UI 是否在冷却 |
| `available(box, check_color, check_cd)` | 通用可用性；**非当前角色**时退化成 `not task.has_cd(box, index)` |
| `resonance_available()` | = `available('resonance', check_color=False)` |
| `liberation_available(check_color=True)` | = `available('liberation', ...)` |
| `echo_available()` | = `available('echo', check_color=False)` |

⚠️ **没有"冷却剩余几秒"的结构化接口**。轴里不能用剩余 CD 做判断，只能靠"能不能用"和
UI 像素。人工在录像里记的"E 剩余 11.4 秒"只是参考信息，别写进代码。

### 2.2 三个技能 helper 的语义

- `click_resonance(post_sleep, has_animation, send_click=True, time_out=0, ...)`
  - 返回三元组 `(clicked, duration, animation)`。
  - `time_out=0` 表示用默认超时 `SKILL_TIME_OUT = 15` 秒；**超时会报错并自动截图**
    （`alert_skill_failed`），所以别拿它当"等一等"用。
  - `send_click=False`：等待期间**不**顺手多打一次普攻。本轴对共鸣技能统一这么用。
- `click_liberation(con_less_than=-1, send_click=False, wait_if_cd_ready=0.1, ...)`
  - `task.use_liberation` 关闭时直接返回 False。
  - `con_less_than > 0` 时，协奏值高于它就放弃释放。
  - 内部会一直等到 `liberation_available()` 变 False，即**等动画/状态结束**。
- `click_echo(duration=0, time_out=1)`
  - `time_out=0` = "可用就发，不等"（召唤型脱手声骸）。本轴对脱手声骸统一用 `time_out=0`。

### 2.3 轴里怎么处理"等不等"

- **要等它放完的**（共鸣解放）→ 依赖 helper 自身的状态等待，再补一个动画兜底时间
  （本轴弗洛洛 `AXIS_LIBERATION_CAST_TIME = 3.30`）。
- **脱手的**（声骸）→ `time_out=0`，只给一个短尾缓冲或不给。
- **动作暂不可用** → 重试间隔 `AXIS_ACTION_RETRY_SLEEP = 0.10`，
  上限 `AXIS_ACTION_WAIT_TIMEOUT`（弗卜维轴：卜灵 `3.0` / 弗洛洛 `1.5` / 维里奈 `1.0`）。
  ⚠️ 上限设太大 → 站桩发呆；设太小 → 该放的技能被跳过。两个方向都出过问题。

---

## 3. 平A 的前摇与后摇

### 3.1 框架层

- `normal_attack()` = `check_combat()` + `task.click()` 一次。
- `heavy_attack(duration=0.6)` = `mouse_down()` → sleep → `mouse_up()`，用于长按型重击。
- `continues_normal_attack(duration, interval=0.1, ...)` = 在一段时间内持续普攻。

### 3.2 每个角色都不一样，必须单独测

| 角色 | 普攻参数 | 来源与性质 |
| --- | --- | --- |
| 弗洛洛 | A1/A2/A3 = `0.67 / 0.60 / 0.53s`（帧表 40/36/32 帧） | 参考包**逐帧数据**，最可靠 |
| 卜灵 | `0.10s` 输入间隔 | 参考实现**等待值**，非帧测 |
| 维里奈 | `0.10s`（`ATTACK_INTERVAL`） | 参考实现**等待值**，非帧测 |

### 3.3 两种"时间"不要混

- **输入间隔**：同一种输入之间能发多快（比如连打平A）。
- **可接动作窗口**：这个动作开始后多久才允许发下一个**不同**动作。

轴里真正卡住的是后者。跑太快 → 输入被吞（表现是"某一下没打出去"）；
跑太慢 → 整体超时、循环错位。弗卜维轴里这两类参数是分开命名的
（`*_INTERVAL` vs `*_CAST_TIME`）。

### 3.4 长按型重击

- 写法：`mouse_down()` → 保持 `duration` → `mouse_up()`。
- **在空中会被打断**，所以重击前先 `if self.flying(): self.wait_down()`；
  被打断要重试（参考实现是 3 次，本轴沿用）。

### 3.5 关于"前摇/后摇"这个词

⚠️ 框架里**没有**独立的"前摇""后摇"API。录像里能看到"闪避取消前后摇"这类现象
（见 `MANUAL_TIMELINE_24FPS.md` 的 `00:00:37:02`），但代码里是用
**"可接动作窗口"**近似表达的。所以讨论前后摇时，最终都要落到"这个动作之后多久能接下一个输入"。

---

## 4. 特殊机制

### 4.1 跳A / 空中攻击

- `flying()`：靠"控物"UI 判断是否在空中。**`task.has_lavitator` 为 False 时永远返回 False**
  —— 所以设置里的 `Check Levitator` 必须开。
- `wait_down(click=True)`：等落地，最多 2.5 秒。
- 标准跳A写法（参考包卜灵，本轴沿用）：

```python
self.task.jump(after_sleep=0.01)
self.sleep(0.05)
if self.flying():
    self.click()
    self.sleep(0.05)
else:
    self.wait_down()
```

- 本轴参数：`AXIS_JUMP_AFTER_SLEEP = 0.01`、`AXIS_JUMP_POST_SLEEP = 0.05`、
  空中普攻后 `AXIS_AERIAL_NORMAL_POST_SLEEP = 0.05`。
- ⚠️ 跳A 的落地时机依赖角色模型和跳跃高度，换角色要重新测。

### 4.2 切人后自动平A

见 1.6。这是最容易漏掉、又直接影响连段计数的一条。

### 4.3 闪避取消

- `闪` = `task.click(key='right')`，前后各留缓冲（本轴 `0.12 / 0.04`）。
- 用途：取消动作后摇并直接接强化动作。弗洛洛的 `3A → 闪 → 强化A` 就是这么打的，
  链内用独立窗口 `0.55s`，和普通闪避接强化A 的 `0.25s` 不同。
- ⚠️ 这条是从录像观察 + 实机调出来的，没有官方帧数据。

### 4.4 协奏 / 延奏

- `is_con_full()` / `get_current_con()` / `current_con`。
- 满协奏切人时 `switch_out(con_full=True)`：会给 buff 计时并清零 `current_con`，
  对治疗者还会写 `last_full_con_switch_time`（触发 1.4 的 16 秒锁）。
- 本轴用 `free_intro` 决定"这次切人算不算变奏入场"。

### 4.5 F 键击破

- `f_break()` / `task.check_f_break()`；`check_f_on_switch` 控制切走前是否自动按 F
  （治疗者默认关闭）。
- ⚠️ 上游注释明确写着：**击破动画带全局时停且目前无法识别，可能出现计时问题**。
  弗卜维轴因此暂不加入 F 键机制。

---

## 5. 调试

- 每个动作前后调 `check_combat()`，战斗结束或角色失效时它会抛出，避免带着脏状态继续跑。
- 弗卜维轴每个动作都会打 `dpv axis phase=<n> step=<n> ...` 的 debug 日志，
  包含阶段、步骤、调用的 helper、实际耗时和结果——实机调参主要看它。
- 时间要用 `time_elapsed_accounting_for_freeze()` 计算，别用裸 `time.time()`，
  否则动画冻结会让计时失真。
