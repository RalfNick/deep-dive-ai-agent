# 第 1 章配套实验

这些小程序对应《深入浅出 AI Agent》第 1 章。每个实验只暴露一个机制，刻意不引入 Agent 框架或远程模型 API。

## 安装

```powershell
cd chapter1
python -m pip install -r requirements.txt
```

依赖采用精确版本。单个脚本保持教学输出简洁；统一环境、命令、输入、随机种子和结论边界由章末的实验报告集中记录。

## 实验 1：Tokenizer

```powershell
python token_demo.py
python token_demo.py "深入浅出 AI Agent"
```

比较字符数、UTF-8 字节数、Token 数、Token ID 与原始字节。程序会打印 `tiktoken` 版本和编码器名称，避免把一次结果误当成跨模型常量。

## 实验 2：因果自注意力

```powershell
python attention_demo.py
```

程序打印 `Q=K=V`、`d_k`、原始分数、因果遮罩、遮罩后的分数、归一化权重和加权结果。每行权重之和应为 1，未来位置权重应为 0。

## 实验 3：Bigram 字符模型

```powershell
python bigram_lm.py --max-new-chars 120
python bigram_lm.py --max-new-chars 240 --seed 9
```

这个程序统计字符转移频率，并没有神经网络的反向传播或优化 step。`--max-new-chars` 表示最多生成字符数；`--steps` 仅作为 `v1.0` 命令的隐藏兼容别名保留一个版本。

## 实验 4：采样与温度

```powershell
python sampling_demo.py
python sampling_demo.py --draws 10000
```

程序保持 Logit 不变，只改变温度。三个中文标签是玩具原子类别，不保证是实际 Token，也不是经过校准的工具动作概率。

## 实验 5：Coding Agent 验证循环

```powershell
python coding_agent_demo.py
```

程序在临时隔离目录中创建失败用例，展示补丁只是模型提议，只有 Harness 写入文件并运行测试后才产生可验证结果。验收同时要求 `"1¥2"` 被拒绝，避免宽松替换将它静默解析为 `12.0`。它是确定性模拟，不调用 LLM，也不修改仓库文件。

## 自动测试

```powershell
python -m unittest discover -s chapter1/tests -p "test*.py" -v
```

测试覆盖 Token 字节可逆性、因果遮罩、温度边界与分布熵、Bigram 固定 seed 可复现性，以及 Coding Agent 修复前后的验收合同。

## 重建实验报告

```powershell
python chapter1/generate_report.py
```

输出保存为 [reports/experiment-results.json](./reports/experiment-results.json)。报告只记录实验需要的版本、控制变量、观察值和证据边界，不记录环境变量、API Key、用户名或临时目录。

生成器默认写入固定的规范快照时间，以保证同一环境连续生成的 JSON 字节一致；调用 `build_report(generated_at=...)` 时仍可显式记录一次独立运行的时间。

## 实验记录模板

每个实验至少记录：

- 精确命令与依赖版本；
- 输入、随机种子与完整输出；
- 本次只改变了哪个变量；
- 观察到什么变化；
- 实验支持哪项结论；
- 实验不能支持哪项结论；
- 一个新的待验证问题。

参考答案与验收标准见 [reference-answers.md](./reference-answers.md)。

## 返回正文

- [第 1 章正文](../book/chapter1.md)
- [第 1 章参考答案](./reference-answers.md)
