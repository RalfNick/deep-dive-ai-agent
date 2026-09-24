# 第 13 章插图生成记录

七幅图使用 `tldraw` 可编辑源文件，遵循全书的浅色纸张、手绘描边和蓝绿紫橙分区风格。技术文字、公式、箭头和连接关系全部由矢量布局生成，未使用生成式图片写字。

## 文件对应关系

| 图号 | tldraw 源文件 | 导出图片 |
| --- | --- | --- |
| 13-1 | `01-evaluation-model.tldr` | `book/images/chapter13/01-evaluation-model.png` |
| 13-2 | `02-same-answer-different-evidence.tldr` | `book/images/chapter13/02-same-answer-different-evidence.png` |
| 13-3 | `03-multi-grader-matrix.tldr` | `book/images/chapter13/03-multi-grader-matrix.png` |
| 13-4 | `05-pass-k-vs-pass-all-k.tldr` | `book/images/chapter13/05-pass-k-vs-pass-all-k.png` |
| 13-5 | `04-eval-lifecycle.tldr` | `book/images/chapter13/04-eval-lifecycle.png` |
| 13-6 | `06-judge-calibration.tldr` | `book/images/chapter13/06-judge-calibration.png` |
| 13-7 | `07-framework-mapping.tldr` | `book/images/chapter13/07-framework-mapping.png` |

`generate_diagrams.py` 是可重复生成的设计源。生成后使用项目固定的 tldraw 导出工具导出 PNG；最终图片为 3127×1806。七图均完成原图检查，其中图 13-3 首版的评分器到门禁连线发生交叉，已改为“多个评分器先汇聚，再进入安全硬门禁”的单一主箭头。

## 视觉自检

- 中文标题、英文缩写和公式无乱码或生成式错字；
- 主流程从左到右，生命周期图按箭头闭环；
- 安全门禁使用醒目的橙色/红色，不与普通分数混淆；
- `pass@k` 与 `pass^k` 的“至少一次”和“全部通过”语义分开；
- 桌面端显示整图；390px 移动端保持 760px 图宽，可在图框内左右滑动并点击查看原图，避免把技术文字压缩到不可读尺寸。
