---
references:
  - ref_id: 01
    filename: refs/01-ref-style.png
    usage: direct
---

Use case: infographic-diagram
Asset type: Chinese protocol comparison diagram
Primary request: Create an original split-screen sequence infographic titled “现代 MCP 与旧版握手模式”. Left blue-mint half heading “现代：2026-07-28” with Client on the left and Server on the right. Show optional dashed request-and-response “server/discover（可选）”, then a solid Client-to-Server direct request card containing exactly “协议版本”, “Client 身份”, “Client 能力”, followed by a Server-to-Client arrow “响应”. Right lavender-orange half heading “旧版：2025-11-25” with Client on the left and Server on the right. Show the exact four-step direction: ① Client → Server “initialize”; ② Server → Client “initialize result”; ③ Client → Server “notifications/initialized”; ④ Client ↔ Server “后续请求与响应”. Across both halves add a small lower band “业务状态：显式 ID + 持久存储”.
Bottom takeaway, verbatim: “现代 MCP 每次请求自描述，旧版靠初始化握手。”
Style/medium: Image 1 style language only—warm cream paper, deep navy hand-drawn strokes, pastel blocks, wobbly arrows, simple Client/Server window doodles.
Composition/framing: landscape 16:9, target 1536×864, perfectly comparable left and right sequences, generous whitespace.
Constraints: dates and protocol labels must be exact; arrow directions are protocol facts and must match the four-step sequence exactly; `server/discover` must look optional, not mandatory; no logos, watermark, photorealism or claim that business state disappears.
