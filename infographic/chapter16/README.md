# 第16章受控技术图

七个独立 Scene 共享第14章的纯 Node/Edge/SVG/Tldraw 渲染器；不会改写第14章。浅纸张、深蓝中文、蓝绿紫橙分区；非生成式栅格图，文字与箭头可机械核对。

在仓库根：`python -B -m infographic.chapter16.generate_diagrams`。结果分别进入本目录可编辑 `.tldr` 和 `book/images/chapter16/` 下 SVG。重复生成字节一致；要修改图，改本章 Scene 并重生，不手改输出。

源含 document/page、合法索引和双端绑定箭头，可拖入 Tldraw 编辑。若已安装 CLI，可向 `chapter16/.runs/` 的新目录导出草图，不需要安装软件；出版 SVG 由受控渲染器导出。SVG 是正文权威图，Tldraw 重排或字体替换可能使草图略有差异。
