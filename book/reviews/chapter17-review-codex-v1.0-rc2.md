# 第 17 章 RC2：新上下文整分支复审处理

日期：2026-09-30。复审范围：`1e95c11..549de84`（RC1 冻结点），按计划与规格只读检查实现、实验、正文、来源、插图、测试和公开边界。审稿者没有修改工作树；实施方对发现重新分级并做**一次**有失败测试的修复流程，没有再派第二轮审稿。本文件记录复审处理，不改写[RC1 作者侧审稿](chapter17-review-codex-v1.0-rc1.md)或 RC1 冻结报告。

## 复审结论与实际修复

复审肯定四幕叙事、七图与实验路径、来源边界、20 案例 RC1 报告的可复现性以及公开清单未变；同时提出 8 项 Important、1 项 Minor，没有 Critical。下列问题都在 RC2 中先用失败测试复现，再修复并重跑章节与全书回归。

| 发现 | 失败证据与 RC2 处理 |
| --- | --- |
| UTF-16 可绕过 ASCII 字节层的 DTD/实体检查 | `test_utf16_entity_document_is_rejected_before_xml_parse` 先得到无问题观察；现先严格按 UTF-8 解码，再拒绝 DTD/实体。只声称此入口拒绝被测声明，不声称已证明所有 XML 解析器都不存在 XXE。 |
| 嵌套 SVG 的 viewport 被扁平当作根坐标 | `test_nested_svg_viewport_cannot_be_flattened_into_root_coordinates` 与后补 `test_nested_allowed_element_is_not_flattened_either` 均曾失败；现只接受扁平受控元素，嵌套坐标空间或其他嵌套元素均 `unknown`。 |
| CSV 重复表头被 `DictReader` 静默覆盖 | `test_duplicate_csv_header_is_unknown_before_dictreader_overwrites_it` 先返回 `answer`；现检查原始 `fieldnames` 恰为 `month,unit,count` 后才构造行字典。 |
| 截图缩小后末端像素被四舍五入到显示区外 | `test_shrinking_edge_pixel_stays_inside_display` 先得到 x=400；现 x/y 分别用整数下取整，800→400 的 x=799 映射 399。 |
| 行动前的帧冒充行动后验 | `test_pre_action_frame_cannot_verify_this_action` 先错误 `verified`；现后验帧采集时间必须晚于本次模拟行动时刻，否则为 `unknown` 且保留 `executed=true`。真实系统仍需行动关联 ID 与业务回执。 |
| 预览依赖未声明 | `test_preview_dependency_is_declared_for_fresh_environment` 先因文件缺失失败；新增 `requirements-preview.txt` 锁定 Markdown 3.10.2，并在 README 说明新环境安装路径。此次复用已有环境，**未做全新环境安装实测**。 |
| `security_violations` 每例硬编码 False | `test_faulty_unauthorized_execution_is_counted_and_cannot_hide_in_report` 注入未授权执行后，旧路径没有合格报告；现固定六类硬门禁由逐案例状态/执行回执计算，报告校验器再次核对，注入会升高违规数。该指标只衡量这些声明的教学不变量，不是通用安全扫描。 |
| 报告未展示规格承诺的失败类型 | `test_group_two_and_five_expose_all_promised_failure_modes` 先缺案例；现组 2 直接展示缺刻度、双图例、缺单位、真实触及 `zero-denominator` 的配套图/CSV；组 5 加入过期图表时间门，报告从 20 扩至 25 例，旧 RC1 报告留存。 |

审稿将练习 17-10 的“删除第四个事件”列为 Minor。实施方把它重评为会改变参考答案的**重要语义歧义**：保留原序号会触发缺号，重新编号才保持后台 `running`。正文和答案分别写明两种情形；这是一次修复流程的一部分，不把新题意偷偷算作旧题答案。

## 范围裁决与剩余边界

审稿者明确不判断真实 VLM/OCR/语音识别质量、真实桌面隔离/补偿、以及恶意并发替换目录的原子沙箱保证。实施方接受这三项为本章**明确未交付**，正文/README/版本记录均限制了外推。代价分别是：不能凭本章数据宣称模型感知质量；不能把模拟器部署为真实动作网关；静态链接/reparse 检查不能替代生产沙箱。若未来转为产品实现，须另立权限、隔离、真实设备及人工验收任务。

## RC2 验收判断

修复后第 17 章 73 项测试、与第 15/16 章及仓库合同合计 336 项和 93 子测试、Node 4 项通过。RC2 两套九文件报告与参考包逐字节一致；25 个固定案例为 `answer=10`、`unknown=11`、`blocked=2`、`refresh=2`，声明的硬门禁违规 0、证据覆盖 25/25。桌面与手机预览仍为七图、五表、零失效锚点和零整页溢出；严格站点构建通过且第 17 章不在公开清单。建议作为**本地 RC2 候选**保留，不宣称模型或生产验收，亦不推送或发布。
