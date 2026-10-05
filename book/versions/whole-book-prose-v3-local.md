# 全书正文清理：editorial-v3-local

日期：2026-10-05。分支：`codex/whole-book-reader-revision`。Git基线：`c8f2995343e90de0721c4236f880c88bbcb3d324`；直接前版为未提交的 `editorial-v2-local`。状态：仅本地编辑候选，未提交、推送或发布。

## 修改范围

清理第1–18章与附录A的阅读编排、作者版本/验收状态、审稿过程、自我评价和重复导览。保留正文技术解释、具体失败样本、公式、图、练习、命令前提、安全边界和官方资料核对日期。没有修改实验实现、图源、规范报告、来源台账、介绍页或公开清单。

版本、审稿与验证元数据留在独立档案，不再穿插正文。第14章原“后续写作地图”链接改为读者可用的全书目录链接。第12/15章文档测试随措辞调整，测试专用历史适配器仍拒绝运行时代码豁免。

## 历史保护

开始前核对上一轮38项哈希，全部匹配后保存43份原文件，包括18章、附录、介绍页、元数据、相关测试和上一轮哈希台账。见 [清理前快照](whole-book-prose-v3-before-2026-10-05/README.md)及 [逐文件哈希](whole-book-prose-v3-before-2026-10-05/snapshot-hashes.json)。

上一轮 `whole-book-reader-v2-hashes.json` 保留原值：它现在描述历史编辑版，应与本轮快照中的对应文件比较，不再要求后来正文与它相同。原28份v2前快照、既有章节版本、Review和发布标签未改写。本版另存 [当前哈希台账](whole-book-prose-v3-hashes.json)。

## 验证环境与结果

Python 3.11.15，pytest 9.0.2，Node 24.15.0。Python验证使用 `PYTHONDONTWRITEBYTECODE=1`、`PYTHONUTF8=1` 与 `-X utf8 -B`，pytest关闭缓存插件；命令从仓库根目录运行，Node渲染测试从 `book/` 运行。Windows原生环境排除沙箱临时目录权限干扰。

| 验证 | 实际结果 |
| --- | --- |
| `python -X utf8 -B -m unittest discover -s tests -p 'test_*.py' -q` | 63项通过 |
| `pytest tests/test_reader_revision_history.py chapter12/tests/test_manuscript.py chapter15/tests/test_manuscript.py -q -p no:cacheprovider` | 28项通过；包含13项历史行为测试 |
| 第3/4/5/6/7/8/10/11章分别 `pytest chapterN/tests` | 20/24/63/143/65/71/42/26项通过；避免同名模块一起收集 |
| 第12章16份无需新增框架依赖的核心测试 | 162项通过；不含Agents SDK/LangGraph框架运行 |
| 第13–18章与附录A测试 | 534项通过，14个子测试通过 |
| 收尾再次运行第15章与附录A | 150项通过，14个子测试通过 |
| `node --test tests/*.test.mjs` | 4项通过 |
| `python -X utf8 -B -m scripts.check_repository --root .` | 退出0 |
| `python -X utf8 -B -m scripts.build_site --root .` 与 `mkdocs build --strict` | 218份公开源，退出0；仅本地构建 |
| 43份快照及上一轮38项历史哈希 | 全部逐字节匹配 |
| 19份正文围栏内代码比较 | 全部一致（统一换行后比较） |

第12章所选核心文件为 `test_backends`、`test_container`、`test_context`、`test_contracts`、`test_delivery`、`test_manuscript`、`test_preflight`、`test_provider`、`test_recovery`、`test_runtime`、`test_sources`、`test_state`、`test_tools`、`test_trace`、`test_verifier`、`test_preview`。

## 整库默认入口限制

完整执行 `python -X utf8 -B -m pytest -q -p no:cacheprovider --tb=short`，在收集阶段退出1，15项错误。没有修改这些范围外的环境/测试问题，也没有据分章结果宣称全书全部测试通过。

缺少NumPy：

- `chapter1/tests/test_experiment_report.py`
- `chapter1/tests/test_sampling_bigram.py`
- `chapter1/tests/test_token_attention.py`

缺少Agents SDK（框架比较另需LangGraph）：

- `chapter12/tests/test_agents_sdk.py`
- `chapter12/tests/test_langgraph.py`

缺少MCP SDK：

- `chapter9/tests/test_experiments.py`
- `chapter9/tests/test_mcp_app.py`
- `chapter9/tests/test_report_reproducibility.py`

同名模块冲突：

- `chapter11/tests/test_exercise_solutions.py`
- `chapter11/tests/test_experiments.py`
- `chapter12/tests/test_experiments.py`
- `chapter12/tests/test_preview.py`
- `chapter13/tests/test_experiments.py`
- `chapter4/tests/test_runtime.py`

夹具被误收集：`chapter12/fixtures/link-checker/tests/test_existing.py` 缺少工作区内 `src` 模块。章节独立运行不采用这份夹具作仓库测试入口。

## 复核与未证明事项

见 [正文/技术复核](../reviews/whole-book-prose-v3-review-2026-10-05.md)。本轮没有重新核对产品资讯，没有执行真实模型、Docker或GPU训练，也未进行真实API与TypeScript编译验证。正文所保留的来源日期不被本次编辑刷新。

公开 `book/manifest.json`、`scripts/build_site.py` 和 `mkdocs.yml` 保持原字节：仍只公开第1–14章，第15–18章和附录没有被自动发布。旧版内容可从快照与既有Git基线恢复。未产生译文或PDF。

