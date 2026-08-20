# 参与贡献

感谢你帮助完善《深入浅出 AI Agent》。本仓库把书稿、实验和证据视为同一个出版单元：改动一个结论时，也要检查支持它的来源、代码、图表、报告和 Non-claims。

## 提交类型

### 正文与图表

- 先说明要解决的读者问题，再解释概念边界、架构、实现和失败模式。
- 快变产品事实优先引用官方一手资料，并在对应 `book/sources/` 台账记录核对日期。
- 新图优先使用可审阅 SVG，避免外链图片、机器绝对路径和未授权素材。
- 不把教学夹具的结果写成模型能力、行业统计或厂商排名。

### 实验与代码

- 先增加会失败的测试，再实现最小修复。
- 每章保持可独立运行，依赖写在自己的 `requirements.txt` 中。
- 固定随机 seed、输入、版本和结论边界；可复现报告连续生成两次应保持一致。
- 不提交 `.env`、API Key、缓存、live provider 输出、PDF 或本机渲染目录。

### 翻译

英文版目前是 `planned`。开始翻译前必须先按 [docs/TRANSLATION.md](docs/TRANSLATION.md) 将状态变为 `active`，固定简体中文源提交，并保持章节文件名、图片、代码引用、Claims 与 Non-claims 对齐。当前不接受繁体中文目录占位。

## 本地检查

按改动范围运行对应命令：

~~~powershell
python -m unittest discover -s tests -v
python -m unittest discover -s chapter1/tests -v
python -m unittest discover -s chapter3/tests -v
python -m unittest discover -s chapter4/tests -v
python -m unittest discover -s chapter5/tests -v
python -m unittest discover -s chapter6/tests -v
~~~

第 2 章没有独立 unittest 套件，请运行其 README 列出的 7 个脚本。涉及规范报告时，连续生成两次并核对 `docs/EXPERIMENT_STATUS.md` 中的哈希。

## Pull Request 说明

请写清：

1. 改动解决什么读者或工程问题；
2. 修改了哪些正文、实验和证据；
3. 实际运行了哪些验证命令；
4. 哪些事情仍未证明或未验证。

不要在 Issue、提交、日志或 PR 中粘贴真实凭据。
