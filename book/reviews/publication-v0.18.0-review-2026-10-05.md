# 全书 0.18.0 发布复核

复核日期：2026-10-05。范围：简体中文18章、附录A、实验/答案/图示、GitHub Pages与个人阅读站点同步实现。编辑冻结点363b05a；旧记录、快照、规范报告与tag保留，不生成译文或PDF。

## 独立审查结论

只读审查最终为 Ready to merge: Yes；无未处理Critical、Important或Minor。核对实际manifest、306源白名单、21份发布哈希、历史元数据适配器，以及博客目录、前后文、阅读进度、SEO、搜索和附录计数。

## 发现与处置

| 发现 | 处置与回归 |
| --- | --- |
| preview requirements无hash却强制hash模式，阻断CI | 新CI安装预览依赖不用hash模式，开发依赖仍强制校验；新隔离环境安装成功，新增workflow检查 |
| 附录真实title包含标签，SEO/search再次添加造成重复 | 保留源title，去重展示前缀；真实title测试由RED转GREEN |
| MkDocs默认TOC丢中文，17章练习fragment失效 | Unicode slugify；实际配置渲染中文anchor和英文兼容测试通过，strict提示消失 |
| Windows git show JSON默认GBK解码失败 | 两处调用显式UTF-8；无UTF8环境开关时9项delivery通过 |

仓库78项、发布专项15项、博客37文件147项测试通过；TypeScript与lint退出0。第12章锁定框架环境210项通过，其余分章结果见[正式记录](../versions/book-v0.18.0.md)。部分审查员沙盒临时文件权限阻断不作为代码失败，主代理与实施者在授权原生环境完成fresh回归。

## 不外推

本复核不代表线上已部署；提交后还需干净同步、CI/Pages及Cloudflare回执和生产URL检查。未评价真实模型、GPU、Docker、设备、翻译或PDF；不以分章通过掩盖默认整库pytest的历史收集限制。
