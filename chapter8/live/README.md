# Chapter 8 可选 Live Probe

规范实验完全离线，不需要 API Key，也不下载模型。本目录只用于回答另一个问题：把固定的 Evidence Packet 交给真实 LLM 后，请求是否能成功、Provider 返回了怎样的原生 usage，以及答案能否通过人工或外部评估。

## DeepSeek 示例

```powershell
$env:DEEPSEEK_API_KEY = "[REDACTED]"
python chapter8/live/live_probe.py --provider deepseek --execute
```

输出默认写入被 Git 忽略的 `chapter8/live-output/live-probe.json`。脚本不会打印或保存凭据；缺少凭据时以 `config_error` 退出。该输出不是规范基准，不会覆盖 `chapter8/reports/`。

真实 Embedding、Cross-Encoder 和 Ragas 可通过核心代码中的 `EmbeddingModel`、`DeterministicReranker` 与评估函数边界替换。它们需要额外依赖和模型下载，因此不进入公共 CI。请分别记录模型标识、依赖版本、数据集版本、原生 usage、延迟和失败状态，不要与固定教学向量合并成一个分数。
