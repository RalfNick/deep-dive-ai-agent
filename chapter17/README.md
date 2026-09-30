# 第 17 章：多模态与实时 Agent 离线实验

这是《深入浅出 AI Agent》第 17 章的自包含教学包。Python 3.11+ 运行时仅用标准库；测试依赖版本及哈希在 `requirements-dev.txt`。默认不需要 API Key、网络、模型、麦克风或真实桌面控制。

从仓库根目录运行：

```powershell
python -B -m pytest chapter17/tests -q
python -B -m chapter17.experiments --group all --output chapter17/.runs/reader-first
python -B -m chapter17.experiments --group 3 --output chapter17/.runs/reader-screen
python -B -m chapter17.exercise_solutions --all --output chapter17/.runs/answers-reader.json
python -B -m chapter17.preview
```

输出目录必须是新的 `chapter17/.runs/` 或 `chapter17/reports/` 子目录；即使已有目录为空也拒绝覆盖。五组结果、十三题答案、总体报告、摘要和 SHA-256 manifest 使用确定性编码。完整 RC1 参考规范包在 `reports/reference-rc1/`；`reports/reference-v1/` 是此前的 16 案例历史样本。实际读者运行建议放 `.runs/`，该目录被 Git 忽略。本地预览只写 `preview-pages/index.html`，也不会进入公开站点。

| 文件 | 作用 |
| --- | --- |
| `fixtures/chart-base.svg` / `chart-truncated-axis.svg` | 两张受控柱状图，展示零轴与截断轴；不是任意 SVG/OCR 解析能力 |
| `fixtures/chart-values.csv` | 独立数值，拒绝冲突、重复月份、混合单位 |
| `fixtures/screens.json` | 合成画面，不含真实桌面截图或真实点击 |
| `fixtures/voice-events.json` | 中性事件日志，不含真实录音或厂商私有事件 |
| `contracts.py` / `chart.py` / `screen.py` / `voice.py` | 来源、观察、决策与三条受控路径 |
| `experiments.py` / `evidence.py` / `output.py` | 五组案例、版本化报告、输出保护 |

本章结果只证明固定教学夹具下的边界行为。图表解析拒绝 DTD、脚本、外链、变换和未知几何；屏幕行动只返回模拟回执；语音事件只归约固定序列。遇到缺数据、过期帧、未授权或未见后验，返回 `unknown`、`refresh` 或 `blocked`，不以最终回复冒充完成。

正文见 [`book/chapter17.md`](../book/chapter17.md)，资料边界见 [`book/sources/chapter17-sources.md`](../book/sources/chapter17-sources.md)。
