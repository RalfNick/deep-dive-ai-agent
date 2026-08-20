# 第 5 章独立 Review：上下文工程——Agent 真正看到的世界

Review 日期：2026-08-16

Review 对象：`book/chapter5.md`、`chapter5/`、`book/images/fig5-*.svg`、`book/sources/chapter5-sources.md`、`chapter5/reports/context-experiments.json`、`output/pdf/chapter5-preview.pdf`。

对照材料：第五章设计文档、实施计划、既有 `book/reviews/chapter5-review.md`，以及前一版写作前设计 Review。

## 一、结论先行

第五章的选题、章节主线和大部分工程实现是成立的，已经具备一本工程型 Agent 教材应有的骨架：同一个 `parse_price()` 案例贯穿全章，概念能够落到本地代码，实验主动暴露失败结果，离线结论与真实模型结论也有明确边界。

但本次独立 Review **不同意现有“没有未解决 P1、可直接作为 v1.0 发布”的判断**。当前建议为：

> **正文结构通过，出版验收暂缓；修复 5 组 P1 后再进入最终发布。**

总体评分约 **7.8 / 10**：

| 维度 | 评分 | 判断 |
| --- | ---: | --- |
| 选题与章节边界 | 9.0 | 与第 4、6、7、8、9 章分工清楚 |
| 读者路径与表达 | 8.8 | 从失败现象到 Pipeline，再到实验和产品映射，路径顺畅 |
| 架构设计 | 8.5 | 类型、来源、权威、信任、敏感、预算基本分离 |
| 实验方法 | 8.0 | 变量隔离意识强，但部分实验退化成合同自证或覆盖范围收缩 |
| 代码与测试 | 8.2 | 50 项本章测试通过，但 Grader 的若干字段没有测到真正语义 |
| 证据一致性 | 6.3 | 正文数字、参考答案、API 工具协议和运行状态存在不一致 |
| 出版与视觉 | 8.8 | 35 页 PDF 整体稳定，7 幅图清楚，无明显排版故障 |

本章最大的问题不是“内容写得不够多”，而是**几个看似已经被测试和评分覆盖的结论，实际没有被相应指标证明**。这类问题比一般措辞瑕疵更值得优先修正。

## 二、做得好的部分

### 1. 开篇问题真实，而且准确指向装配层

开头没有用“上下文工程很重要”作泛泛介绍，而是让读者看到：模型没看到失败测试、工具描述过于含糊、输入中还混入噪声与注入，此时把失败全部归咎于模型是不成立的。这个张力能自然导出全章问题：

> 谁把什么信息，以什么身份、什么顺序、什么预算交给了模型？

这是很好的章节主问题，也与第 4 章 Harness Engineering 的结尾形成了真实接口，而不是只靠过渡句连接。

### 2. 概念边界比常见“Prompt 技巧合集”清楚

正文把 Prompt、Context、Context Window、Context Engineering、Memory 和 RAG 分开，尤其是“存着不等于看见”“看见不等于真实”两句话，能够有效阻止读者把会话历史、向量库和模型窗口混为一谈。

章节也没有提前写完后续内容：单次调用前的装配留在本章，长任务压缩、Checkpoint、Memory 和 RAG 分别留到第 6—8 章，完整工具协议留到第 9 章。这一范围控制是合理的。

### 3. 数据模型基本落实了写作前 Review 的关键建议

最终实现没有把所有属性压成一个 `priority` 或“相关性分数”，而是分开建模：

- `ContextKind`；
- `InstructionAuthority`；
- `TrustLevel`；
- `RetentionPriority`；
- `Sensitivity`；
- `Scope`；
- `Provenance`；
- `required_for`。

`ContextPacket + ContextBuildTrace` 双输出也已落地。Trace 默认不保存候选正文，Secret 使用 `redacted` 且不记录精确长度，这一修订是有价值的。

### 4. 对实验外推边界的态度严谨

正文多次明确：

- `RuleBasedProbe` 只能证明本仓库合同，不代表真实神经模型；
- 信息位置实验只完成变量隔离，没有复现普遍的 Lost-in-the-Middle；
- UTF-8 字节不是 Token；
- Prompt 分隔符不是沙箱；
- Provider 错误不能进入模型行为分母；
- 当前没有真实 DeepSeek 结果，不能做产品或模型排名。

这比用一次 API 输出制造“规律”可靠得多。噪声实验保留 100% 无关项时，正文也没有隐藏失败，而是让 `BuildGrade.passed=false`，这种诚实值得保留。

### 5. 执行边界复用了第 4 章，而不是重新发明一套安全故事

`.env` 注入变体故意让 Probe 产生危险提议，再由 `ToolCallFactory` 重建 Harness 所有的标识，最后交给第 4 章 `ActionGateway.evaluate()`。正文也明确说明这只是策略接口，不是 OS 沙箱证明。章节之间因此形成了真实代码依赖。

### 6. 视觉层面已经接近出版质量

独立渲染并检查了 35 页 A4 PDF：

- 7 幅图均能正常显示；
- 表格、代码块和脚注没有明显横向裁切；
- 中文、英文和行内代码未出现乱码或黑块；
- 页眉、页码、标题层级和实验卡片风格统一；
- 图 5-4、5-5、5-6、5-7 在页面尺寸下仍可辨认。

最后一页注释下方留白较多，但属于内容自然结束，并非空白页或排版断裂，不构成发布阻断项。

## 三、P1：出版前必须修复

## P1-1：正文练习与参考答案已大面积错位

这是当前最直接的出版阻断项。

正文 `book/chapter5.md:864-883` 的 14 道题与 `chapter5/reference-answers.md` 并非同一版本。只有少数题目能够一一对应，多数编号已经漂移：

| 编号 | 正文问题 | 当前参考答案 | 状态 |
| ---: | --- | --- | --- |
| 1 | 定义 Prompt、Context、Window、Context Engineering、Memory、RAG 六个概念 | 只回答前三个概念 | 不完整 |
| 2 | 网页中的 `SYSTEM:` 为什么不能获得权限 | authority 与 trust 为什么不能合并 | 错题 |
| 3 | authority 与 trust 的区别 | 两个 Digest 的区别 | 错题 |
| 5 | 去重 Trace 实验 | 预算过紧 | 错题 |
| 6 | 100—1400 的预算曲线 | 删除权限排序 | 错题 |
| 7 | 目录作用域实验 | 位置实验 | 错题 |
| 9 | 真实模型位置探针 | `.env` 注入与 Gateway | 错题 |
| 10 | 多租户规则覆盖合同 | 新增企业 Wiki 来源 | 错题 |
| 11 | Secret 工具的运行时凭据注入 | 多租户 Scope | 错题 |
| 12 | 跨部门事实冲突 | 429 为什么不是模型错误 | 错题 |
| 13 | 反驳只靠系统 Prompt 的安全说法 | Digest 缓存 | 错题 |
| 14 | 20 条 Context Fixture 的评估设计 | 什么时候不需要 Builder | 错题 |

现有自审报告称“14 道练习包含可观察验收标准，参考答案与代码路径对应”，这个结论不成立。

建议：以正文题目为唯一主版本，逐题重写参考答案；每题至少包含判断依据、代码入口、运行命令或验收条件。增加一个静态测试，提取正文与答案中的题号和标题，要求 `1..14` 完整对应，避免以后再次漂移。

## P1-2：工具描述实验没有经过 API 原生工具协议，却借用了原生工具调用结论

当前离线实验测到的是：`RuleBasedProbe` 在序列化后的普通文本里查找固定字符串 `required arguments: path, old, new`，找到后构造一个硬编码 `ToolProposal`。这能验证教学 Probe 的字符串合同，但不能验证真实模型的 function/tool selection。

真实 `DeepSeekAdapter` 也没有发送 API 原生 `tools` 数组：

- `chapter5/context/serialization.py:69-82` 的请求只有 `model`、`messages`、`temperature`、`max_tokens`、`response_format`、`thinking` 和 `stream`；
- `ContextPacket.tools` 只是工具名称元数据，工具说明被放在普通 Context Section 文本中；
- `chapter5/probes.py:274-288` 只解析 `choices[0].message.content` 中的自定义 JSON；
- Adapter 不解析官方 `message.tool_calls`。

而 DeepSeek 当前官方 Chat Completions 文档所说的“description 用于选择何时和怎样调用函数”，对应的是请求中的原生 `tools[].function.description`，响应也有 `message.tool_calls`。参见 [DeepSeek Chat Completions API](https://api-docs.deepseek.com/api/create-chat-completion/)。

因此，正文 `book/chapter5.md:388` 的“本章 Adapter 同时满足这两条”和实验四对官方 function description 的引用会让读者误以为本实现走了原生工具协议。

有两种可接受的修法：

1. **推荐：补齐原生工具适配。** `PacketSerializer` 生成 `tools` 数组，DeepSeekAdapter 解析 `tool_calls`，再对 vague / precise / negative 三种描述进行真实探针；自定义 JSON 决策仍可用于非工具状态。
2. **收窄结论。** 明确将实验命名为“文本化工具合同实验”，删掉“本 Adapter 满足原生工具描述接口”的说法，并说明它没有验证 API function calling。

如果保持当前代码，实验四支持的最强结论只能是：**固定 Probe 会对一段包含所需参数名的文本作出不同反应。**

## P1-3：Grader 有两个“显示已评分、实际未形成门禁”的字段

### Build 冲突评分只是重复 ID 检查

`chapter5/graders.py:149-151` 当前实现为：

```python
conflict_ok = len(result.packet.selected_item_ids) == len(
    set(result.packet.selected_item_ids)
)
```

这只能证明选中 ID 没有重复，不能证明：

- 高权威指令是否获胜；
- 事实冲突是否两边可见；
- 未解决的 Tool Schema 是否全部拒绝；
- Trace 是否给出正确的 `conflict_lost/conflict_visible`；
- 版本替代是否选中了正确版本。

更重要的是，`BuildGrade.passed` 的表达式没有包含 `conflict_ok`。即使该字段为 `false`，总门禁仍可能通过。

### 不可信指令提升没有触发 Safety 硬失败

`SafetyGrader` 会计算 `untrusted_instruction_promotions`，但 `hard_failures` 只加入 Secret 泄漏、Trace 泄漏和 Gateway 漏判。也就是说，如果恶意内容被错误放到可信指令区，但这次恰好没有生成危险路径，`SafetyGrade.passed` 仍可能是 `true`。这与设计文档“恶意内容未被提升是安全结论必要条件”直接矛盾。

此外，当前实现用“Payload 任意位置是否出现 `BEGIN_UNTRUSTED_DATA`”判断是否隔离。如果另一个 Section 有分隔符，而真正的 hostile Section 没有，仍可能被误判为已隔离。`injection_followed` 也只是“本次存在 hostile 候选且最终路径危险”，不是对具体恶意 item 的因果归因。

建议：

- 给每个实验变体显式传入冲突期望：赢家 ID、保留集合、丢弃集合与期望 reason；
- `BuildGrader` 逐项检查这些期望，并把冲突合同纳入 `passed`；
- Serializer 输出 item/section 级边界证据，SafetyGrader 检查 hostile item 是否位于对应分隔区，而不是全局查字符串；
- `untrusted_instruction_promotions > 0` 必须成为安全硬失败；
- 把 `injection_followed` 表述为“与夹具标记相关的行为观察”，不要写成已经完成严格因果证明。

## P1-4：缺少 API Key 时没有生成 `skipped` 或结构化失败报告

写作前设计和 `book/sources/chapter5-sources.md:62` 都要求：真实探针不可用时应记录 `SKIPPED` 或结构化 Provider 错误，不能与任务失败混在一起。

实际运行：

```powershell
Remove-Item Env:DEEPSEEK_API_KEY -ErrorAction SilentlyContinue
python -m chapter5.experiments.run_all --live --repeats 1 `
  --output tmp/chapter5-missing-key-review.json
```

结果是 `CredentialMissing` traceback、退出码 1，且没有报告文件。原因是 `chapter5/experiments/run_all.py:34` 在构建任何 `CaseRecord` 前直接调用 `DeepSeekAdapter.from_environment()`，异常未被转换成运行级状态。

当前测试 `test_from_environment_requires_explicit_key` 只证明 Adapter 会拒绝空 Key，没有验证 CLI 是否履行“结构化记录”的实验合同。

建议增加运行级 `SKIPPED`/`CONFIG_ERROR` 结果，至少保存：运行日期、requested model、`total_attempts=0`、`valid_decisions=0`、原因 `missing_credential`。401/403、429、超时和非法响应继续作为已经发起请求后的基础设施失败。不要为缺 Key 伪造 28 次请求失败。

## P1-5：预算手算数字与当前 Fixture 不一致，并混淆两类 Required

正文 `book/chapter5.md:287-305` 声称：

```text
pricing.py                    82
test_pricing.py               49
apply_patch tool schema      105
合计                         236
```

按当前代码的 UTF-8 字节算法重新计算，实际为：

| 条目 | 当前字节数 | `required_for` |
| --- | ---: | --- |
| `pricing.py` | 60 | `source-file` |
| `test_pricing.py` | 39 | `currency-test` |
| `apply_patch` | 104 | `tool-schema:apply_patch` |
| 合计 | 203 | 三项 requirement |

同时，Builder 的“required bucket”还包含 `retention_priority=REQUIRED` 但不满足上述 requirement 的两项：

| 条目 | 当前字节数 | 原因 |
| --- | ---: | --- |
| `system-context-contract` | 69 | retention required |
| `task-template-1` | 86 | retention required |

因此预算 180 时真正选中的是 system + task，共 155 units；三项 requirement 全部缺失。`ContextPacket.required_budget` 当前记录的是“已选 required bucket 的成本”155，不是“满足所有 requirement 所需成本”203，也不是“五项 required bucket 总成本”358。

这不只是三个数字过期，还暴露了命名问题：

- `retention_priority=REQUIRED` 表示条目不应被普通可选信息挤掉；
- `required_for` 表示条目能满足某个任务 requirement；
- 二者不是同一概念；
- `required_budget` 的读者语义不明确。

建议从 Fixture 自动生成正文表格或至少增加断言；将字段重命名为 `selected_required_units`，并另报 `requirement_evidence_units` / `all_required_candidate_units`。正文必须展示 system、task 与三项证据的完整竞争关系，不能只用已经失效的三项手算解释 `tight_budget`。

## 四、P2：建议本轮一并修正

### P2-1：指令冲突实验比设计合同窄

设计文档原计划交叉改变高权限规则、用户要求和不可信内容的位置；用户最初的实验设想还包含 system、用户请求、仓库规则和工具结果冲突。

当前五个变体实际是：

- SYSTEM 与 REPOSITORY 同源冲突，交换候选输入顺序；
- hostile Artifact 放在最前或最后；
- 两条 Fact 冲突。

没有用户约束与仓库规则冲突，也没有 Tool Observation 与自然语言指令/事实冲突。`SourcePolicy` 还把整个 `user_request` 固定分类为 `TASK + authority=NONE`，因此当前模型无法表达“用户消息中既有任务事实，又有较低权威指令”的混合结构。

建议至少补两个变体：

1. 用户要求与仓库规则冲突，验证用户任务不能越过更高层安全规则，同时保留合法目标；
2. 工具观察与文本陈述冲突，验证 Observation 作为高 trust 事实没有获得 instruction authority。

如果不补，就把章节和设计文档的范围收窄为“同一稳定来源身份内的 SYSTEM/REPOSITORY 冲突示例”。

### P2-2：Provider 消息角色映射没有成为显式合同

`PacketSerializer.to_messages()` 除最小 Harness 合同外，把所有 Context Section 都发送为 `role=user`。因此 `authority=system/developer/repository` 目前只是正文中的 Harness 元数据，不是 Provider 的 system/developer role。

这并非必然错误：Builder 可以在发送前解决冲突，Claude Code 官方也公开说明项目规则可能作为用户消息进入上下文。但本章应明确区分：

- Harness 内部 authority；
- Provider message role；
- 模型可见的元数据标签；
- 外部强制执行权限。

建议增加 `ProviderRoleMapper` 或在 Serializer 合同中明示映射策略，并测试高权威内容不会因错误映射进入不可信数据区、低权威内容不会被提升到 system role。

### P2-3：新鲜度进入了定义和生产建议，却没有进入当前 Builder 或限制清单

正文定义强调来源和新鲜度，`Provenance` 也保存 `observed_at`，但当前 Builder 不使用 `observed_at` 判断过期，只做显式版本替代。生产指标又建议记录过期来源数量。

教学实现可以不做完整时效策略，但“本章真正证明了什么”和已知限制中应明确加入：**当前代码记录时间，不评估时效；旧观察是否失效仍由上游或未来策略决定。** 否则读者容易把 `observed_at` 的存在误解为已经完成 freshness control。

### P2-4：`SafetyGrade.passed=true` 与“模型已安全”之间还需更强措辞隔离

当前安全通过只代表：指定 Secret 字符串没有进入默认序列化 Payload/Trace，危险路径被当前 Gateway 规则拒绝。它不覆盖：

- Secret 的编码、分片、摘要或语义泄漏；
- 非路径类危险参数；
- 网络、进程、数据库和外部 API 工具；
- Gateway 绕过路径；
- 模型输出中的隐私复述；
- OS 级副作用。

正文已有部分限制说明，建议把报告字段命名为 `fixture_safety_contract_passed`，或在 Schema 中保留 `scope`，避免下游把通用 `passed=true` 当成系统级安全认证。

## 五、P3：编辑与台账问题

### P3-1：测试数量台账过期

`book/sources/chapter5-sources.md:83` 写“48 项测试”，实际独立运行发现 50 项。`book/versions/CHAPTER_VERSIONS.md` 写 50 项，两个台账不一致。

建议让发布脚本从 unittest 输出生成版本记录，不手填数量。

### P3-2：README 与正文的 DeepSeek 核对日期不一致

`chapter5/README.md` 写适配器按 2026-08-15 核对，正文和来源台账写 2026-08-16。统一即可。

### P3-3：当前第五章工作树内缺少 `book/OUTLINE.md`

来源台账称本章以 `book/OUTLINE.md` 为范围依据，但当前独立工作树没有该文件。主工作区有一份未纳入当前工作树的版本。合并前应确保目录文件进入同一版本历史，否则发布 tag 无法独立重建“章节与总纲一致”的证据。

### P3-4：现有双视角自审应保留，但结论需要更新

`book/reviews/chapter5-review.md` 记录了此前真正完成的修订，内容有保留价值；不要覆盖它。建议新增本报告后的 remediation 记录，并把“没有未解决 P1”改为历史时点结论或明确标注“已被独立 Review 补充”。

## 六、五组实验逐项判断

| 实验 | 当前判断 | 做得好的地方 | 修改重点 |
| --- | --- | --- | --- |
| 5-1 装配消融 | 有条件通过 | complete / missing / duplicate / tight budget / restored 结构完整；缺信息转成状态 | 修正预算数字和 Required 语义；增加自动生成成本表 |
| 5-2 指令冲突 | 有条件通过 | 输入顺序归一、指令与事实冲突分治合理 | 增加用户要求、工具观察变体；让 Grader 真正检查冲突结果 |
| 5-3 信息位置 | 通过 | 三个模板 × 三个位置，集合不变、顺序摘要变化；没有虚构模型规律 | 真实模型实验继续保持探索性，不需要为出版强行调用 |
| 5-4 工具描述 | 暂缓通过 | 主动承认长度未控制，负面约束不替代网关 | 补 API 原生 `tools/tool_calls`，或把结论降为文本合同实验 |
| 5-5 噪声与注入 | 有条件通过 | 噪声质量失败没有被隐藏；Secret 和 Action Gateway 分层正确 | 修复 Safety promotion 门禁与 item 级分隔检查；扩展非路径风险 |

其中实验三是当前方法学最干净的一组：它没有试图让确定性 Probe 模拟神经模型，而是把“可用于未来真实探针的严格对照输入”作为产物。实验四则是最需要收口的一组，因为当前固定 Probe 的决策规则直接查找被操纵的描述字符串，若不接入真实原生工具协议，很容易形成循环证明。

## 七、自动验证与独立复现记录

### Python 与报告

| 验证项 | 结果 |
| --- | --- |
| `python -m unittest discover -s chapter5/tests -v` | 50 / 50 通过 |
| `python -m unittest discover -s chapter4/tests -v` | 24 / 24 通过 |
| `python -m chapter5.experiments.run_all --output ...` | 生成 28 条记录 |
| 报告分母 | 28 attempts / 28 valid decisions / 0 infrastructure failures |
| 原报告 SHA-256 | `5D5A5FD1BF555E6D7D1AA0C1D6995C58450880BD756A1CEABBAA94BF5FF0AF73` |
| 重复生成 SHA-256 | 与原报告一致 |
| 缺少 Key 的 `--live` | 退出码 1，抛 traceback，不生成结构化报告 |

离线报告的 28 个变体分布为：

- 装配消融 5；
- 指令冲突 5；
- 信息位置 9；
- 工具描述 3；
- 噪声与注入 6。

报告中预期失败的 Build 记录有：`missing_required`、`tight_budget`、`injection_secret`、`noise_5`、`noise_20`。这些失败本身合理；问题在于部分 Grader 字段没有检验其名称声称的合同。

### Markdown、图与 PDF

| 验证项 | 结果 |
| --- | --- |
| 正文非空字符 | 28,256 |
| 二级 / 三级标题 | 26 / 3 |
| 原创图 | 7，路径均存在 |
| 脚注 | 14 个定义，无未定义引用 |
| `book` 渲染门禁 | 4 / 4 通过 |
| PDF | 35 页，A4，约 1.10 MB |
| 全页缩略图检查 | 无空白页、乱码、明显裁切或重叠 |
| 关键页原尺寸复核 | 图、表、代码和注释可读 |

自动测试全部通过说明实现具有较好的确定性和回归基础，但不能抵消本报告中的 P1：那些问题正是“测试断言与读者以为被证明的语义没有对齐”。

## 八、与写作前设计 Review 的对照

写作前建议中，以下内容已经较好落地：

- authority、trust、retention 分离；
- `ContextPacket + ContextBuildTrace` 双输出；
- Secret 在预算前过滤；
- Build / Decision / Safety 分层；
- `.env` 提议经过第 4 章网关；
- Provider 故障与行为分母分离；
- 噪声与注入拆成两个子实验；
- 实验不保存 API Key，不用单次模型结果声称普遍规律。

仍未完全落地的项目：

- Grader 分层有字段，但部分字段未形成真实门禁；
- 缺 Key 没有变成 `skipped` 或结构化失败；
- 指令冲突矩阵没有覆盖用户请求与工具结果；
- 工具描述没有进入原生 API Tool Schema；
- Provider 角色映射没有独立合同；
- freshness 只有元数据，没有策略；
- 参考答案没有随最终练习同步。

因此，这一章不是推倒重写，而是需要一次**证据合同收口**。

## 九、建议修改顺序

### 第一批：先修会让读者得到错误结论的问题

1. 同步 14 道题与参考答案；
2. 修正文预算数字，澄清两类 Required 和 `required_budget`；
3. 修复 Build/Safety Grader 的假门禁，并先添加失败测试；
4. 让缺 Key 产生运行级结构化结果。

### 第二批：决定工具实验的最终定位

5. 在“接入原生 `tools/tool_calls`”与“收窄为文本合同实验”中做明确选择；
6. 若接入原生工具协议，重新生成真实 Probe 的请求摘要合同和测试；
7. 修正文、README、来源台账对实验四的支持/不支持结论。

### 第三批：补齐方法学与台账

8. 增加用户指令与工具观察冲突变体；
9. 明示 Provider role 映射和 freshness 未实现边界；
10. 同步测试数量、核对日期、OUTLINE 和版本记录；
11. 重新生成报告、PDF 与新版本哈希；
12. 更新既有自审结论并进行一次独立复核。

## 十、再次 Review 的验收清单

- [ ] 正文 1—14 题与答案 1—14 题逐题对应；
- [ ] 预算表由当前 Fixture 计算，正文数字与代码一致；
- [ ] `required_budget` 含义更名或在合同中无歧义；
- [ ] 冲突结果错误时 `BuildGrade.passed=false`；
- [ ] hostile item 被提升时 `SafetyGrade.passed=false`；
- [ ] Safety 分隔检查绑定到具体 hostile item/section；
- [ ] 无 Key 的 `--live` 生成结构化 skipped/config 记录；
- [ ] 工具实验明确使用原生 API 工具协议，或明确不声称 function calling；
- [ ] 指令冲突至少覆盖 system/repository/user/data-observation 的代表性组合；
- [ ] freshness 未实现被列入限制，或补充明确时效策略；
- [ ] Chapter 5 及 Chapter 4 回归测试继续通过；
- [ ] 28 条离线报告重复生成仍然字节一致；
- [ ] 来源台账、README、版本记录中的测试数和日期一致；
- [ ] 新 PDF 逐页无裁切、重叠、乱码和失配脚注；
- [ ] 发布为新版本，不覆盖已有 v1.0 历史证据。

## 十一、最终判断

第五章已经是一章**方向正确、可读性强、工程味足**的内容，且比常见的 Context Engineering 文章更重视来源、权威、敏感边界、Trace 和失败分层。它不需要扩成更大的概念百科，也不需要为了“显得真实”仓促调用一次商业模型。

当前真正需要的是把五处证据错位修正：

1. 练习与答案必须属于同一版本；
2. 工具描述实验必须诚实对应实际协议；
3. Grader 的字段必须真的检验它声称的语义；
4. 可选 API 缺失必须留下结构化状态；
5. 正文数字必须由当前代码和报告支撑。

完成这些修订后，本章可以进入正式出版版本；在此之前，更合适的状态是：

> **内容 Review 有条件通过，发布门禁未通过。**
