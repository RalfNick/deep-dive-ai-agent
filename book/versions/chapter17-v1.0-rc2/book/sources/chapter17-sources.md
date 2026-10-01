# 第 17 章资料与证据台账

核对日期：2026-09-30（Asia/Shanghai）。本章把论文、官方产品说明和本地固定实验分开；链接指向原始论文或官方文档。产品页面会变化，读者应以阅读当日版本复核。下表“不能支持的外推”是引用边界，不是对资料质量的评价。

| 编号 | 来源及版本/定位 | 本章用途 | 不能支持的外推 |
| --- | --- | --- | --- |
| C1 | [ChartQA: A Benchmark for Question Answering about Charts with Visual and Logical Reasoning](https://arxiv.org/abs/2203.10244)，arXiv:2203.10244，2022 | 图表问答同时需要视觉定位与逻辑/算术推理；理解为什么读柱形和计算不能混成一句话 | 不证明本章的受限 SVG 解析器能解真实图片，也不代表某模型当前成绩 |
| C2 | [ChartQAPro: A More Diverse and Challenging Benchmark for Chart Question Answering](https://arxiv.org/abs/2504.05506)，arXiv:2504.05506，2025 | 说明真实信息图、仪表板与不可回答问题会加大评估难度；引出弃答 | 论文数据和模型比较不移植成本章小样本准确率；不据此排名当前产品 |
| C3 | [ScreenSpot-Pro: GUI Grounding for Professional High-Resolution Computer Use](https://arxiv.org/abs/2504.07981)，arXiv:2504.07981，2025 | 指出专业软件高分辨率、小目标的视觉定位问题，帮助解释帧、坐标和目标框 | 不证明本章合成屏幕能代表真实 GUI 分布，也不证明所画坐标有模型定位能力 |
| O1 | [OpenAI Images and vision](https://developers.openai.com/api/docs/guides/images-vision)，官方指南，2026-09-30 核对 `Limitations` | 官方列举小字、旋转、图表视觉样式、精确定位、计数及缩放等局限；支持保留不确定性 | 不能推出“所有模型都会在本章图上答错”或精确误差率 |
| O2 | [OpenAI Realtime conversations — Interruption and Truncation](https://developers.openai.com/api/docs/guides/realtime-conversations#interruption-and-truncation)，官方指南，2026-09-30 核对 | 区分用户开始说话、响应取消、客户端停播和删除未播出的对话内容；WebRTC/SIP 与 WebSocket 的缓冲责任不同 | 不能把中断事件等同于应用后台任务取消；本章中性事件名不是厂商协议的原样复制 |
| O3 | [OpenAI Computer use](https://developers.openai.com/api/docs/guides/tools-computer-use)，官方指南，2026-09-30 核对 | 模型提出 UI 操作，由应用提供环境、执行动作并回传截图/结果；多动作须按顺序处理 | 不证明本章代码使用 OpenAI 工具，也不保证沙箱、审批、坐标缩放自动由 API 完成 |
| O4 | [OpenAI Getting started with GPT-Live](https://developers.openai.com/api/docs/guides/live)，官方指南，2026-09-30 核对 | 语音前台与后台委派职责分离，应用检查权限、确认并保存进度；后台可在打断后继续，由应用决定是否取消 | 不表示所有 Realtime API 会话都采用 GPT-Live，或某个打断自动撤销副作用 |
| A1 | [Anthropic Computer use tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool)，官方指南，2026-09-30 核对 | Claude 提出截图、鼠标、键盘工具请求，应用在受控环境执行；官方安全注意事项包括隔离、最小权限和人工确认 | 工具版本、模型覆盖范围会变化；不能把本章模拟器说成 Anthropic 工具的正式实现或安全认证 |
| L1 | [本章受限 SVG 与独立 CSV 夹具](../../chapter17/fixtures/chart-base.svg)、[图表代码](../../chapter17/chart.py)，本分支 RC1 | 80→100、零/截断轴、歧义与冲突的可复算本地事实 | 不支持真实 OCR、多图表类型或视觉模型能力结论 |
| L2 | [RC2 固定报告](../../chapter17/reports/reference-rc2/report.json)、[运行入口](../../chapter17/experiments.py)，Schema `chapter17.multimodal.v1` | 25 个确定性案例的状态、证据与覆盖分母；所有正文实验数值以运行报告为准，RC1 旧报告仍保留 | 不支持真实 Token、费用、语音延迟、真实桌面安全性或跨模型胜负 |

**资料使用规则。** 引文只支持其直接陈述的机制或研究问题。实验结果单独来自本仓库代码和夹具。论文 benchmark、官方功能说明、作者设计判断三者不能互相冒充。没有真实 Provider Usage 时不补造成本与 Token；没有模型接入时不报模型正确率；没有录音和真实屏幕时不报实际感知能力。产品页名称或工具版本未来变化时，以链接中的当日官方文档为准，并更新本台账核对日期。
