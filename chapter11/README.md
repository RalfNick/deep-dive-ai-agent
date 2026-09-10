# 第 11 章：Coding Agent 的仓库工作台

配套正文：[Coding Agent：代码库就是它的环境](../book/chapter11.md)。当前为 **v1.0-rc2 本地候选**，未发布。rc1 书稿与代码保留在 Git 提交 2ad0791，旧规范报告另存于 [rc1 报告目录](reports/versions/v1.0-rc1/repository-work.md)。

## 先运行完整修复

需要 Python 3.11+ 和 Git。在本书仓库根目录运行，不需要 API Key，也不安装模型 SDK：

```bash
python --version
git --version
python -m chapter11.quickstart
python -m unittest discover -s chapter11/tests -v
```

quickstart 在临时目录建立教学 Git 仓库，运行后自动清理该临时目录。不会修改本书正文或你的业务仓库。输出依次包含：

- initial_tests：3 项测试通过，但独立验收发现嵌套链接错误。
- red：加入回归后 4 项测试、1 项失败。
- final：修复后 4 项通过，独立行为检查通过，accepted=true。
- diff：活动源码的一行修改，以及新增回归测试。

这里的“修复”由固定程序序列完成。没有模型推理，也不是对 Claude Code 或 Codex 的运行成绩。

red.details 保存失败测试名、异常类别和期望/实际值差异；stdout、stderr 独立保留，普通 print 不再破坏结果解析。repair 只在确认目标回归失败后冻结测试并修复；测试意外全绿、导入错误或其他失败会以 unexpected_red 中止。子进程未产出有效报告时，count 为 null，不冒充“零项测试”。临时结果文件不是安全边界，输出也没有生产级容量限制。

## 五组实验

```bash
python -m chapter11.experiments --group repair
python -m chapter11.experiments --group instructions
python -m chapter11.experiments --group conflict
python -m chapter11.experiments --group verification
python -m chapter11.experiments --group resume
```

| 组 | 观察 |
| --- | --- |
| repair | 旧测试通过、回归失败、修复通过的完整过程 |
| instructions | 项目约定文件清单变化；不测产品加载与遵循 |
| conflict | 读取后源码改变，旧摘要补丁被拒绝 |
| verification | 覆盖不足、零项测试、断言移除都不能验收完成 |
| resume | 旧交接记录保持原值，但当前证据有效性变为 false |

[JSON 规范报告](reports/repository-work.json) 与 [阅读版报告](reports/repository-work.md) 来自实际文件、Git 和子进程操作。重新生成会覆盖这两份规范报告，因此修改实验之前先提交或另存旧版：

```bash
python -m chapter11.experiments --output chapter11/reports
```

也可以将 --output 指向新的目录，保留规范报告不变。规范输出不含临时绝对路径、时间戳或随机提交号。

## 留一个工作区自己操作

```bash
python -m chapter11.prepare chapter11/live-reports/manual-repo --with-guidance
```

只允许新目录或空目录；已有内容会报 not_empty，不会覆盖。它创建一个独立教学仓库；后续 Git 命令应在该目录运行。live-reports 已被本书忽略，请自行决定是否另行保存观察结果，不要把真实令牌或隐私日志放进去。

[产品观察指南](product-walkthrough.md) 给出完整 Codex 手动路线、Claude Code 对应入口与记录模板。[参考答案](reference-answers.md) 对应正文 14 题。机器可执行的边界断言见 [test_workbench.py](tests/test_workbench.py)、[test_experiments.py](tests/test_experiments.py) 和 [Review 回归测试](tests/test_review_regressions.py)。

## 直接运行第 6–10 题

回到本书仓库根目录，任选一条；每题自行建立临时教学现场，不依赖前一题：

```bash
python -B -m chapter11.exercise_solutions 6
python -B -m chapter11.exercise_solutions 7
python -B -m chapter11.exercise_solutions 8
python -B -m chapter11.exercise_solutions 9
python -B -m chapter11.exercise_solutions 10
```

第 9 题预先声明新的缺失链接合同，再做红绿修复，并验证“恒空返回”仍被拒绝；不会覆盖标准五组报告。完整上下文见 [exercise_solutions.py](exercise_solutions.py)，预期输出见参考答案。

## 代码阅读顺序

1. [workbench.py](workbench.py)：夹具、摘要、受限补丁、测试和验收。
2. [experiments.py](experiments.py)：固定步骤怎样产生观察。
3. [quickstart.py](quickstart.py) 与 [prepare.py](prepare.py)：运行入口。

工作台只面向本书生成的可信夹具，不是恶意仓库沙箱。补丁摘要检查与写入之间没有跨进程锁；验收会导入并执行仓库代码；摘要未绑定 Python、依赖、环境变量或远端状态。不要把这些机制直接当作生产安全保证。

## 可选 HTML 预览

```bash
python -m pip install -r chapter11/requirements-preview.txt
python -m chapter11.preview
```

生成 chapter11/preview-pages/index.html，图片仍引用仓库内资源。预览文件不提交 Git，也不会自动修改公开网站。移动预览时需要一起保留书籍目录结构。
