---
references:
  - ref_id: 01
    filename: refs/01-ref-style.png
    usage: direct
---

Use case: infographic-diagram
Asset type: Chinese technical book landscape diagram
Primary request: Create an original hand-drawn architecture infographic titled “Function Calling、Tool Runtime 与 MCP”. On the left, a blue “模型 / Function Calling” zone shows “工具定义 → 调用提议”. In the center, the largest mint “Host / Agent Runtime” zone shows four responsibilities “Schema 校验”, “Policy”, “Loop / State”, and “Verifier”. From this Runtime, split into two alternative execution paths, never a single sequential chain: upper path “本地 Handler → Result / Receipt”; lower path “MCP Client → MCP Server → Server Runtime / Handler → Result / Receipt”. Both Result paths return to the central Runtime with clear return arrows. Inside the MCP Server, show three small capability labels “Tools / Resources / Prompts”.
Bottom takeaway, verbatim: “Function Calling 产生提议，Runtime 负责控制，MCP 负责连接。”
Style/medium: use Image 1 only as style reference: warm cream paper, deep navy hand-drawn outlines, pastel blue/mint/lavender/orange, rounded cards, subtle wobble, neat Chinese handwritten print. Do not copy its subject or exact layout.
Composition/framing: landscape 16:9, target 1536×864, readable proposal zone, large central control zone, and two clearly parallel execution paths with ample whitespace.
Constraints: render every listed label exactly; MCP is an alternative connection path from the Host Runtime, not a stage after execution; no product logos, vendor ranking, watermark, footer account, photorealism or extra prose. Avoid implying MCP executes actions by itself.
