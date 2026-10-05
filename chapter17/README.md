# 第 17 章：多模态与实时 Agent 离线实验

2026-10-05：已随全书 `0.18.0` 公开，正式版本说明见[本次记录](../book/versions/chapter17-v1.0.md)。以下离线范围与旧候选记录继续保留。

这是《深入浅出 AI Agent》第 17 章的自包含教学包。Python 3.11+ 实验运行时仅用标准库；测试依赖版本及哈希在 `requirements-dev.txt`，本地 HTML 预览与完整测试还需 `requirements-preview.txt` 中锁定的 Markdown 3.10.2。独立环境请先安装这两份依赖；只运行实验无需预览依赖。默认不需要 API Key、网络、模型、麦克风或真实桌面控制。

若使用全新虚拟环境做完整测试与预览，先运行 `python -m pip install -r chapter17/requirements-dev.txt` 和 `python -m pip install -r chapter17/requirements-preview.txt`；只复现五组实验不需要安装这两份开发依赖。

从仓库根目录运行：

```powershell
python -B -m pytest chapter17/tests -q
python -B -m chapter17.experiments --group all --output chapter17/.runs/reader-first
python -B -m chapter17.experiments --group 3 --output chapter17/.runs/reader-screen
python -B -m chapter17.exercise_solutions --all --output chapter17/.runs/answers-reader.json
python -B -m chapter17.preview
```

输出目录必须是新的 `chapter17/.runs/` 或 `chapter17/reports/` 子目录；即使已有目录为空也拒绝覆盖。五组结果、十三题答案、总体报告、摘要和 SHA-256 manifest 使用确定性编码。当前 RC3 参考规范包在 `reports/reference-rc3/`；RC2 的 25 案例包、RC1 的 20 案例包和更早的 `reference-v1/` 均原样保留。RC2 正文、七图与答案快照见 `book/versions/chapter17-v1.0-rc2/`。实际读者运行建议放 `.runs/`，该目录被 Git 忽略。本地预览只写 `preview-pages/index.html`，也不会进入公开站点。

| 文件 | 作用 |
| --- | --- |
| `fixtures/chart-base.svg` / `chart-truncated-axis.svg` | 两张受控柱状图，展示零轴与截断轴；不是任意 SVG/OCR 解析能力 |
| `fixtures/chart-values.csv` | 独立数值，拒绝冲突、重复月份、混合单位 |
| `fixtures/screens.json` | 合成画面，不含真实桌面截图或真实点击 |
| `fixtures/voice-events.json` / `voice-interruption.json` / `voice-task-cancel.json` / `voice-conflict.json` | 完整事件及三种实际案例输入；每种序列绑定独立摘要，不含真实录音或厂商私有事件 |
| `contracts.py` / `chart.py` / `screen.py` / `voice.py` | 来源、观察、决策与三条受控路径 |
| `experiments.py` / `evidence.py` / `output.py` | 五组案例、版本化报告、输出保护 |

本章结果只证明固定教学夹具下的边界行为。图表限定 520×380 的零原点 viewport、已知实色柱形与元素层，拒绝 DTD、脚本、外链、变换、裁切与被测隐藏/遮盖形式；这不是通用 SVG 渲染或可见性判定。屏幕行动只返回模拟回执。语音分别维护生成、播放、尾部与后台状态：`response_cancel_requested` 是请求，`response_cancelled` 是生成取消确认，二者都不代替 `playback_stopped`。报告 `details.event_source` 与对应 `evidence_ids` 指向实际事件文件；`source_proof` 摘要可以重算。遇到缺数据、过期帧、未授权或未见后验，返回明确状态，不以最终回复冒充完成。

正文见 [`book/chapter17.md`](../book/chapter17.md)，资料边界见 [`book/sources/chapter17-sources.md`](../book/sources/chapter17-sources.md)。
