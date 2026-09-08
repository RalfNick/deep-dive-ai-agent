# 第十章插图生成与校对记录

工具：内置 imagegen；用途：scientific-educational / infographic-diagram。风格沿用用户确认的米白纸纹、深蓝手绘轮廓、蓝绿紫橙浅色分区、清楚中文手写印刷字。不是对受版权保护图片的复制，也不使用他人 logo。

## 通用提示

生成原创中文技术教材信息图，竖版 3:4，米白纸面与轻微铅笔纹理，深海军蓝手绘轮廓，低饱和蓝绿紫橙圆角面板。清晰大中文，手机可读，留白充足。只把指定画面文字印到图上，不印布局指令；无水印、logo、装饰性乱码。状态箭头与下述语义严格一致。

## 图 10-1：工具集合

标题：工具很多，不必一次全部看见。副标题：注册 ≠ 可发现 ≠ 本轮加载。注册目录 300 个定义，经当前权限过滤为可发现目录 299 个定义；退款工具未授权，不展示。搜索“查询 订单 状态”，本轮加载订单查询和物流查询两份完整定义。底部：加载之后，调用前仍要再查权限与版本。

校对修订：移除第一轮图中误印的“内 / 300张抽象工具卡片”布局文字，三层标题不加引号。原始输出不作为正文版本发布。

## 图 10-2：搜索、加载、调用

标题：找到工具，到真正执行。三面板：搜索（用户需求→授权目录→候选摘要）；加载（名称与版本、完整参数合同、上下文预算，超预算缩小候选）；执行（调用提议→权限再查→版本再查→业务服务，已撤权或已过期则拒绝）。底部：搜到不等于授权，加载不等于执行。

## 图 10-3：有限并发

标题：不是一起发出，就会更快。三面板：独立读取 A/B 同时开始，C 在槽位释放后开始，并发上限 2；依赖链查询订单→获得物流编号→查询物流；异序返回 call-B、call-A、call-C，通过按 ID 对齐得到 A/B/C 对应结果。不能画 B 指向 A 的逐行箭头，使用一个组间总箭头。底部：保留成功的读取，不悄悄吞掉失败。

## 图 10-4：持久作业

标题：请求结束，工作还在。接受：用户提交→保存作业→返回作业号，先保存再回应。执行：queued→running→succeeded；running 可失败或进入 cancel_requested→cancelled。只画常见路径，省略重试回边。继续查询：断开、重连都围绕同一数据库作业号，查询状态、进度、结果。底部：后台执行 ≠ 忘记它；需要查询与恢复。

### v1.1 图内范围标注

输出：`fig10-4-durable-job-v1.1.png`。使用内置 imagegen 编辑，保留 `fig10-4-durable-job.png` 作为旧图。新图已目检：原三面板、六个状态和箭头保留，绿色面板明确说明它只画常见路径；完整分支在正文状态表中展开。

实际编辑提示词：

> Edit target: attached existing book infographic. Preserve the entire cream paper texture, hand-drawn Chinese lettering, blue/green/purple/orange sections, every icon and all arrows and all existing text. Make ONLY this change: replace the green middle section heading '2 执行' with '2 常见状态路径' and place a clearly readable smaller subtitle directly below that heading: '示意图，非完整状态图'. Adjust spacing minimally so no overlaps. This qualification is essential: this diagram deliberately shows only common paths, not all retry/cancellation transitions. Do not add or remove any state boxes or arrows. Preserve portrait aspect ratio and quality. No watermark, no extra text.

## 图 10-5：超时与取消

标题：没等到，不等于没做完。三个独立场景：停止等待但作业继续；提交前请求取消，提交检查点确认取消，没有写入结果；结果已提交后取消，仍然成功。底部：超过作业截止时间，拒绝新的结果提交。不得画撤销已发生事实的回滚箭头。

## 图 10-6：五类标识

标题：这些编号，各认一件事。五张独立卡片，不连接为执行流程：action_key 同一意图重试复用；job_id 恢复后不变；attempt 重新领取加一，旧代次不能提交；seq 记住读到哪里，断线后补读；artifact_id 定位已提交结果，读取仍需授权。底部：一个编号不能同时代表意图、尝试和成品。
