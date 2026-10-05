# 附录 A 配套：先跑通，再理解，再接模型

对应[正文](../book/appendix-a.md)。2026-10-05 随全书 `0.18.0` 公开；实验以原 RC1 为基线，见[正式记录](../book/versions/appendix-a-v1.0.md)。

## 最短入口

从仓库根目录、已确认的Python 3.11–3.13解释器运行：

```powershell
python -X utf8 -B chapter3/agent_loop.py
python -X utf8 -B -m appendix_a.preparation --inspect
python -X utf8 -B -m appendix_a.preparation --group all --output appendix_a/.runs/reader-first
python -B -m unittest appendix_a.tests.test_preparation -v
python -X utf8 -B -m appendix_a.exercise_solutions --all
```

核心练习和14项核心测试只用标准库；不安装包、不读取模型凭据、不联网。输出目录必须是appendix_a/.runs或appendix_a/reports下的**新子目录**，已有目录拒绝覆盖。真实主机观察为stdout-only，稳定报告用固定夹具，不注入时间、机器路径、模型费用或随机ID。

| 组 | 观察 | 边界 |
| --- | --- | --- |
| environment | env-A安装/env-B运行的固定反例 | 不是对读者电脑的扫描 |
| python | JSON解析、预算验证、await观察 | 不证明任意外部输入的生产安全 |
| api | 四条请求草图、401/429/超时分类 | 没有传输功能，不是API连通性测试 |

主机自检单独使用--inspect；supported_python对应根pyproject范围，虚拟环境不是强制通行证。草图的reader-model是占位符，不可当实际模型ID。

## 本地预览与额外交付验证

预览另需Markdown==3.10.2，锁定说明在[requirements-preview.txt](requirements-preview.txt)。已准备好依赖后：

```powershell
python -B -m unittest discover -s appendix_a/tests -v
python -B -m infographic.appendix_a.generate_diagrams
python -B -m appendix_a.preview
node book/check_appendix_a_preview.mjs
```

全部22项测试包含预览/图源/公开构建边界；Node运行检查在未安装Node时跳过，已安装时须使用支持本示例原生类型剥离的版本（Node 22.18及以上受支持版本）。Node 18/20不能直接运行这些.ts示例；若暂不升级，可只运行上面的14项标准库核心测试。浏览器视觉检查复用book已有Playwright与本机Edge，未安装时可跳过，不默认下载浏览器。图片最终在book/images/appendix-a；配对.tldr和生成说明在infographic/appendix_a。

正常TypeScript示例可由支持类型剥离的Node运行：node appendix_a/examples/task.ts。故意错误的unchecked.ts运行输出31，展示“运行不是类型检查”。本轮未运行tsc；已有编译器的读者可自行检查。

规范包：[reports/reference-rc1/manifest.json](reports/reference-rc1/manifest.json)。[参考答案](EXERCISE_ANSWERS.md)、[来源](../book/sources/appendix-a-sources.md)、[审稿](../book/reviews/appendix-a-review-codex-v1.0-rc1.md)、[版本记录](../book/versions/appendix-a-v1.0-rc1.md)共同说明已证明和未证明的内容。

## 真实模型

本包不提供发送开关。正文的SDK代码是依赖/账户自行准备后可选执行的配置示意，本轮未运行；不记录任何真实密钥。第9章live_probe默认dry_run，冻结旧模型默认值，不能宣称已验证当前Provider能力。需要发送时，应在独立私有实验中先核对当前官方资料、授权、预算和实际所需功能。
