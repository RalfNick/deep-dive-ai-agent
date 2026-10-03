# 附录 A 来源与本地证据台账

核对日期：2026-10-03，Asia/Shanghai。正文为独立原创解释，命令依据本仓库实际入口；外部资料只用官方来源，不据模型名或价格作排名。可变文档记录核对日，没有将未下载的网页声称为固定快照。

## 外部来源

| 来源 | 核对方式与范围 | 用于正文 | 不外推的内容 |
| --- | --- | --- | --- |
| [Python Downloads](https://www.python.org/downloads/) | 打开官方安装入口 | 获取Python的可信入口 | 不把当前最新版本当成本仓库验证版本 |
| [Python 3.11 venv](https://docs.python.org/3.11/library/venv.html) | 实际打开How venvs work/创建说明 | 独立包目录、可不激活、重建而非复制环境 | 不是操作系统沙箱 |
| [Python 3.11 JSON](https://docs.python.org/3.11/library/json.html) | 打开转换与解析说明 | dumps/loads、JSON类型、语法与业务验证边界 | 不宣称任意大小不可信输入安全 |
| [Python Coroutines and Tasks](https://docs.python.org/3.11/library/asyncio-task.html) | 打开官方协程入口说明 | 普通脚本asyncio.run与await | 不证明并行性能 |
| [Python Packaging安装指南](https://packaging.python.org/en/latest/tutorials/installing-packages/) | 打开解释器/安装工具说明 | python -m pip、环境对应 | 不把单个requirements等同跨平台全锁定 |
| [Node原生TypeScript](https://nodejs.org/learn/typescript/run-natively) | 打开并定位Type stripping/Type checking/Constraints | 可擦除语法入口、运行不是检查 | 不声称全部TS语法直接运行 |
| [npm ci，CLI v11](https://docs.npmjs.com/cli/v11/commands/npm-ci/) | 打开并定位Description | 需要锁文件、不一致失败、移除node_modules | 本轮未执行安装 |
| [OpenAI Quickstart](https://developers.openai.com/api/docs/quickstart#install-the-openai-sdk-and-run-an-api-call) | 官方文档搜索后fetch对应节 | Responses最小SDK配置示意 | 没有冻结或调用页面模型示例 |
| [OpenAI Authentication](https://developers.openai.com/api/reference/overview#authentication) | 官方文档fetch认证节 | 凭据在服务端注入，不暴露在客户端 | 不访问账户、Key或组织配置 |
| [OpenAI Python SDK](https://developers.openai.com/api/reference/python) | 官方域打开并定位Retries/Timeouts | timeout/max_retries参数、SDK重试层 | 未执行真实SDK请求 |
| [OpenAI Error Codes](https://developers.openai.com/api/docs/guides/error-codes) | 官方文档fetch实际页面 | 区分速率、余额/支出上限、连接错误 | 不靠状态码确认模型已执行 |
| [DeepSeek Your First API Call](https://api-docs.deepseek.com/guides/codex) | 实际打开；该地址本轮返回官方起步页 | 两种兼容入口、Chat最小结构 | 不冻结示例模型或价格 |
| [DeepSeek Responses Guide](https://api-docs.deepseek.com/guides/responses_api/) | 直接打开超时；从已打开起步页链接16成功取得全文，核对兼容表 | Responses存在，input与无状态/忽略参数边界 | 不宣称OpenAI能力完全等价 |
| [DeepSeek Error Codes](https://api-docs.deepseek.com/quick_start/error_codes/) | 直接打开超时；从起步页链接5成功打开 | 参数/认证/余额/速率区别 | 没有真实触发远端错误 |
| [Claude API Overview](https://platform.claude.com/docs/en/api/overview) | 实际打开API/authentication段 | 原生Messages、版本头及认证路线 | 不把x-api-key写成唯一认证方式，不混同云平台 |

OpenAI资料先使用可用官方文档搜索与fetch，SDK参数补充核对官方API Reference。DeepSeek部分直接请求超时，使用官方导航中的真实链接打开成功后才据内容写作。没有根据搜索片段推断接口可用性，也没有把网页打开成功当作Provider调用成功。

## 本地证据

| 文件/入口 | 实际核对 | 支撑结论 |
| --- | --- | --- |
| [根pyproject](../../pyproject.toml) | Python >=3.11且<3.14，根依赖为空 | 推荐3.11起步不等于推荐最新版本；安装根项目不装齐18章 |
| [第3章入口](../../chapter3/agent_loop.py) | 运行完成，4次工具调用、2项目标测试、accepted验证；实验包20项测试通过 | 无密钥离线起步，临时工作区不改正文 |
| [第13章说明](../../chapter13/README.md)及锁文件 | 核对实际requirements-dev.txt，不使用不存在的requirements.txt | 章节安装入口以该章合同为准 |
| [第9章live说明](../../chapter9/live/README.md)和实现 | 默认dry_run，不读取Key；execute才可能网络调用；无model/base-url CLI覆盖参数 | 旧模型默认值不是当前模型验证证据 |
| [附录核心](../../appendix_a/preparation.py) | 固定3组、JSON验证、4请求路线、保守错误分类、独占报告目录 | 本地教学合同，不提供传输 |
| [附录测试](../../appendix_a/tests/test_preparation.py) | 14项核心标准库检查 | 参数拒绝、离线边界、报告重现 |
| [附录交付检查](../../appendix_a/tests/test_delivery.py) | 8项额外检查 | 预览路径、图源/锚点、Node夹具、候选图片不被公开收集 |
| [图源生成器](../../infographic/appendix_a/generate_diagrams.py) | 四Scene产生8文件，图3锚点分散；PNG实际审读 | 技术文字由矢量布局控制，不使用生成式错字图 |
| [本地浏览器检查](../check_appendix_a_preview.mjs) | 1440/390双宽度4图4表、无失效锚点/页面溢出/远程请求 | 本地版式验收，不是生产兼容性验收 |

## 更新规则

后续更新接口事实时，重新打开对应官方资料并记录日期；不能只修改日期冒称复查。真实调用独立记录实际模型/SDK/端点/尝试与脱敏错误；Key和响应中的私密内容不进仓库。规范报告固定夹具另存版本，不覆盖reference-rc1。
