# My-okww 工作区

这个仓库只保存自己的鸣潮（OKWW）配队轴研究成果。上游 ok-ww 的完整代码不再放进本仓库。

## 目录结构

- `ok-wuthering-waves-custom/axis_douling_phrolova_verina/` —— 弗卜维（卜灵 / 弗洛洛 / 维里奈）轴的按版本交付包。
  每个版本一个文件夹，内含 `Douling.py`、`Phrolova.py`、`Verina.py`、`team.json`、`TIMING.md`、
  `MANUAL_TIMELINE_24FPS.md`、`PROGRESS_<版本>.md` 和 `角色资料/`；同名 zip 是可导入 OKWW 的成品包。
  **1.2.0 是当前权威版本。**
- `ok-wuthering-waves-custom/弗卜维_施法时序_1.0.7.zip`、`..._1.0.8.zip`、`..._1.1.0.zip` ——
  早期打包时落在 checkout 根目录的成品包。axis 目录里没有 1.0.7 / 1.0.8 的 zip，1.1.0 的 zip 与 axis 目录内的不是同一份。
- `ok-wuthering-waves-custom/src/char/Douling.py`、`Phrolova.py`、`Verina.py` 和 `config.py` ——
  最初导入时的“可运行 checkout”改动快照，停在 1.0.x。之后所有调整只写在 axis 目录，这里没有同步过，
  不要把它当作当前版本。
- `Augusta_Baizhi_Buling_4_1.0.0/` 及同名 zip、`Cantarella_Mornye_Phrolova_楽山_1.0.0/`、
  `Hiyuki_Lucilla_Verina_a38999_1.0.0.zip` —— 其他配队的角色文件与成品包。
- `弗坎洛轮椅-*.wwcombo.json` —— 连招轴导出文件。

## 上游代码

上游 ok-ww 源码不纳入版本管理（`ok-wuthering-waves/` 已写进 `.gitignore`）。需要对比或实机运行时，在本仓库旁边克隆一份：

```bash
git clone https://github.com/ok-oldking/ok-wuthering-waves.git ok-wuthering-waves
```

然后把需要的角色文件覆盖进那份 checkout 的 `src/char/`。

## 弗卜维轴要点

- 固定队伍：`char_douling`、`char_phrolova`、`char_verina`。
- 自定义状态机在任务层（`_dpv_axis_state`），其他队伍仍走原本的角色逻辑。
- `Verina C2` 在 `config.py` 里配置；只有实际是 C2 维里奈时才置为 true。
- `1.2.0` 暂不加入 F 键机制。
- axis 目录里的文件不会被 OKWW 自动加载，它们是交付快照；实机运行要把三个 `.py` 放进 checkout 的 `src/char/`。
- 历史文件 `弗卜维.zip` 保留原样，不假定它带有当前版本的 `team.json` 导入清单。
- `TIMING.md` 的手工时间线表是时序依据；`AXIS_*` 常量是实现层面的取值。

## 验证状态

静态校验可用 checkout 自带的 Python 环境执行（需先安装依赖）。实机验证仍未完成，改动时序前先在有风险可控的目标上试。
