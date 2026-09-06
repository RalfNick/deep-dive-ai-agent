# Chapter 8 可选 Live Probe

规范实验完全离线，不需要 API Key，也不下载模型。本目录只用于回答另一个问题：把固定的 Evidence Packet 交给真实 LLM 后，请求是否能成功、Provider 返回了怎样的原生 usage，以及答案能否通过人工或外部评估。

## DeepSeek 示例

```powershell
$env:DEEPSEEK_API_KEY = "[REDACTED]"
python chapter8/live/live_probe.py --provider deepseek --execute
```

输出默认写入被 Git 忽略的 `chapter8/live-output/live-probe.json`。脚本不会打印或保存凭据；缺少凭据时以 `config_error` 退出。该输出不是规范基准，不会覆盖 `chapter8/reports/`。

真实 Embedding、Cross-Encoder 和 Ragas 目前只有核心接口和扩展方向，尚未交付完整可运行适配器。本目录的 Live Probe **只验证固定 Evidence Packet 到真实 LLM 回答这一步**，不会训练或下载编码器，也不会将固定语义向量换成真实 Embedding。若自行扩展，需要另外安装依赖、锁定模型版本，并记录数据集版本、原生 usage、延迟和失败状态；不要把新结果与固定教学向量合并成一个分数。
