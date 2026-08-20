# 第 2 章实验：训练、偏好、采样、推理与模型 API

本目录包含七个不需要 API Key 的可复现实验。六个机制实验只依赖 Python 3.11+ 标准库；`real_sft_evidence.py` 使用固定版本 NumPy，真正训练两个微型神经语言模型并生成曲线。它们用于观察中间状态，不用于比较真实厂商。

## 运行

~~~powershell
cd chapter2
python sft_mask_demo.py
python real_sft_evidence.py
python preference_demo.py
python sampling_demo.py
python reasoning_budget_demo.py
python structured_output_demo.py
python model_selection_demo.py
~~~

真实 SFT 实验会更新以下可审计产物：

- `results/real_sft_curves.csv`：每 10 步损失曲线；
- `results/real_sft_summary.json`：seed、上下文、词表与最终指标；
- `../book/images/fig2-7-real-sft-curves.svg`：正文使用的曲线图。

## 实验与结论边界

| 文件 | 可观察内容 | 能支持的结论 | 不能支持的结论 |
| --- | --- | --- | --- |
| `sft_mask_demo.py` | 移位标签、`-100` 遮罩、有效位置损失 | 同一对话可对应不同优化目标 | 遮罩方案一定适合所有模型 |
| `real_sft_evidence.py` | 真实梯度、目标成功率、保留集损失 | SFT 目标与保留能力必须联合评估 | 微型字符 MLP 代表大模型收益 |
| `preference_demo.py` | chosen/rejected 的相对间隔与 DPO 损失 | DPO 直接优化相对偏好 | 偏好标签等于客观真相 |
| `sampling_demo.py` | greedy、temperature、top-p 的频率 | 采样改变既有概率和候选集合 | 低温度等于真实或安全 |
| `reasoning_budget_demo.py` | 搜索预算、已展开节点和成功率 | 更多测试时计算有成本且会饱和 | 迷宫 BFS 等价于 LLM 内部推理 |
| `structured_output_demo.py` | 语法、Schema、语义、策略四层结果 | JSON 合法不等于业务可执行 | Schema 能代替权限控制 |
| `model_selection_demo.py` | 硬门槛、容量与 Pareto 前沿 | 先过滤不可行配置，再比较取舍 | 教学夹具可用于真实厂商排名 |

脚本中的数据均固定。随机实验使用显式 seed；同一 Python/NumPy 版本和平台应得到相同或数值非常接近的结果。若升级 NumPy、BLAS 或解释器，应重新生成并记录环境。

## 返回正文

- [第 2 章正文](../book/chapter2.md)
- [第 2 章参考答案](./reference-answers.md)
