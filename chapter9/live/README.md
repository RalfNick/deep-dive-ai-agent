# 可选 Provider Live Probe

本目录用于观察不同 Provider 如何表达同一条工具调用，不参与规范实验报告。默认命令完全离线：

```bash
python -m chapter9.live.live_probe --provider deepseek
```

只有同时提供环境变量并显式加入 `--execute` 才会发起网络请求：

```bash
python -m chapter9.live.live_probe --provider deepseek --execute
python -m chapter9.live.live_probe --provider openai --execute
python -m chapter9.live.live_probe --provider anthropic --execute
```

对应环境变量分别为 `DEEPSEEK_API_KEY`、`OPENAI_API_KEY` 和 `ANTHROPIC_API_KEY`。不要把任何 Key 写进命令、配置示例或 Git。Live 输出只写入已经被忽略的 `chapter9/live-reports/`，并移除 Provider 响应 ID 与请求头。

