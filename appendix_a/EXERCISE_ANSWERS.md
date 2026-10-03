# 附录 A 分层练习参考答案

三组共9题。完整正文见[附录 A](../book/appendix-a.md)。答案入口：在根目录运行 `python -X utf8 -B -m appendix_a.exercise_solutions --all`。全部离线；本文件中的类型检查与真实调用是可选要求，不冒充已经执行。

## 第一组：定位层次

### A-1：包已安装，仍导入失败

比较安装解释器与运行解释器。运行 `python -c "import sys; print(sys.executable)"` 和 `python -m pip --version`。若使用明确的虚拟环境路径，两条命令都换成同一解释器前缀。安装在env-A、运行在env-B时，A中的成功不证明B有包。不要打印环境变量全集，它可能包含凭据。

### A-2：脚本路径重复

站在chapter3中，再写chapter3/agent_loop.py，相当于寻找嵌套的一层。可在该目录使用 `python agent_loop.py`，或返回根目录再使用原命令。先观察当前目录，不修改源码为机器绝对路径。

### A-3：not_run不是远端通过

root_ok只证实本地标记文件存在，not_run明确未调用Provider。还需在有授权、有预算的条件下收到实际响应，记录对应Provider、模型和配置；即使成功，也只覆盖那个请求，不是应用全部能力验收。

## 第二组：数据与语言

### A-4：序列化与解析

字典→dumps→字符串str→loads→字典dict，恢复后的max_steps=3。答案程序实际执行这两个转换，不只打印手写类型名。

### A-5：预算输入

3接受；字符串“3”拒绝；true拒绝；0拒绝。后3种都返回invalid_budget。Python的bool属于int子类，因此本合同用精确类型检查，并限制1至10。JSON能解析只完成语法检查；若业务确实要接受字符串，应另行明确规范化规则，而不是偷偷转换。

### A-6：31与类型检查

Node移除 `: number` 后执行字符串拼接，得到31。若已有TypeScript编译器，`tsc --strict --noEmit appendix_a/examples/unchecked.ts` 应指出类型不匹配；本轮未运行编译器，不写成实测诊断。正常配置文件仅包含task.ts，故意错误文件不进入正常工程类型检查集合。

## 第三组：接口证据

### A-7：协议与兼容

Responses最小草图使用input；Chat Completions使用messages列表。本附录例子中提示、模型占位符相同，但完整端点与请求形状不同。地址改对后还需验证工具调用、流式终止、错误与会话语义。服务忽略一个不支持的参数时，小请求可能仍返回成功，所以“不报错”不是参数生效证据。

### A-8：三种429

原因码明确为rate_limit_exceeded：bounded_retry，遵守服务提示和预算。credit_balance_exhausted等账户类原因：check_account，等待不是解决办法。没有原因码：inspect_error_code，先查错误结构。分类器只输出建议，没有实际发起重试。

### A-9：安全的首次调用记录

保留Provider、协议、端点、模型ID、SDK版本、实际尝试次数、延迟、已脱敏原因码，必要时保留经审查的请求ID。排除密钥、完整认证头、敏感提示、个人信息；若要记录正文，另行审核。

超时写“未收到明确结果，服务端收到状态未知”，不写“服务端未执行”。请求可能已产生费用；若Agent同时执行外部动作，还可能已有副作用。先核对SDK和应用重试，再决定下一次尝试。回放记录不是重新执行动作的授权。
