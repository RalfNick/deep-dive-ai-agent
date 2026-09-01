---
references:
  - ref_id: 01
    filename: refs/01-ref-style.png
    usage: direct
revision_from: infographic.md
revision_reason: "The first candidate incorrectly repeated a receipt after model context."
---

Use case: scientific-educational
Asset type: Chinese security engineering landscape infographic, corrected second render
Primary request: Create an original left-to-right “security gates” infographic titled “工具调用失败地图”. A proposed call begins at a speech bubble “模型提出工具调用（提议）”, then travels through exactly eight hand-drawn gates: “1 JSON 解析”, “2 Schema”, “3 Registry”, “4 Host Policy”, “5 Server Policy”, “6 Executor”, “7 Result / Receipt”, “8 模型上下文”. Under the gates show the matching concise risks in exactly this order: “格式错误”, “参数注入”, “未知 Tool”, “未同意”, “越权”, “业务错误 / 超时未知”, “错配 / 伪造”, “结果注入 / 数据外泄”. After gate 8, show only a small decision fork labeled “继续 / 停止”. Never show another receipt after model context. Result / Receipt must appear exactly once, at gate 7.
Bottom takeaway, verbatim: “格式正确只是起点，安全执行需要多道边界。”
Style/medium: use Image 1 only for visual language—warm cream paper, deep navy hand-drawn lines, macaron blue/mint/lavender/orange zones, slightly wobbly gates and arrows. Original composition; do not copy reference content.
Composition/framing: landscape 16:9, target 1536×864, strong left-to-right reading direction, eight clearly separated gates, short labels, ample whitespace. Keep the final decision fork fully inside the canvas.
Constraints: all labels exact and readable; no extra output scroll, no “执行结果（回执）” after model context, no logos, watermark, photorealism, cyberpunk styling, vendor names or extra risk claims.
