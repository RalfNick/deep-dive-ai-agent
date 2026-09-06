# 第一章总览图 v2：编辑与核验记录

日期：2026-09-06。通过内置 image_gen 编辑，旧图保留，新资产为 `book/images/fig1-0-how-llms-work-v2.png`。

核验：候选与 Logit 一一对应，T=1 概率按采样脚本四舍五入；选中项与追加项均为“读取”；去除 Sigmoid 曲线与不精确柱形刻度；标注玩具词表和概念架构。图不是厂商内部模型结构。

## 初次编辑提示词

Use case: scientific-educational. Edit the attached book infographic, retaining the cream paper, hand-drawn Chinese lettering, blue/green/purple/orange four stacked panels, overall portrait layout, title and style. Produce a polished readable Chinese book figure. Essential corrections: panel 3 must show ONE vector labelled '最后位置的隐藏表示' -> Linear -> a three-row logit table explicitly labelled '读取 2.0', '调用 1.0', '删除 0.1' -> a box labelled 'Softmax · T=1' containing only text '指数化后归一化' (NO S-shaped sigmoid curve) -> three probability bars labelled '读取 0.659', '调用 0.242', '删除 0.099'. Bars proportional .659,.242,.099. These are the ENTIRE toy vocabulary: no ellipses here and no additional logits or probability entries. Clearly put small note '三候选玩具词表，数值经四舍五入' beneath this panel. Selection label '本次选中' with token '读取'. In panel 4 the appended token also becomes '读取', so the sequence is Agent 会 使用 工具 读取. This is illustrative token generation, not execution. Keep stop conditions 结束 Token / 长度限制 / 工具调用. In panel 1 add tiny note '分词与 ID 仅为示意'. For panel 2 keep Transformer Block × N but replace the messy disconnected residual wiring inside dashed rectangle by a clean conceptual line '因果自注意力 → 残差与归一化 → 前馈网络 → 残差与归一化'; no disconnected plus bubbles, no fake circuit wires. Beneath this line put '注意力读取可见前文；前馈网络逐位置变换' and '具体归一化顺序随架构变化'. These are conceptual modules, not an exact PreNorm circuit. Keep readable Chinese and generous whitespace. No logos, watermark, or extra slogans.

## 刻度修订提示词

Edit ONLY the probability chart inside panel 3 of this book infographic. Keep ALL Chinese text, numeric values, style, paper, panels 1, 2 and 4, and all other layouts unchanged. The chart's bar lengths are not aligned with the axis. Replace the entire probability chart and its axis with a clean THREE-ROW TABLE with heading '概率分布', displaying exact rows '读取 | 0.659', '调用 | 0.242', '删除 | 0.099'. No bars, no coordinate axis, no tick labels, no curve. Preserve the adjacent logits table with 2.0,1.0,0.1, Softmax T=1 box and selected token 读取. This avoids approximate visual scales while preserving correct probabilities. Keep original portrait resolution and hand-drawn editorial look.
