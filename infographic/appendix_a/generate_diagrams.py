"""Four original scenes: editable tldraw sources and controlled Chinese SVG."""
import json
from pathlib import Path
from infographic.chapter14.generate_diagrams import Scene, Node, Edge, _point, _svg, _tldraw


def n(key, label, x, y, color, w=300, h=130):
    return Node(key, label, x, y, w, h, color)


def scenes():
    return (
        Scene("01-checkpoints", "先跑通，再理解，再接模型",
              "四个检查点，分别增加一种证据；上一层通过，不代表下一层通过。",
              (n("run", "① 离线程序\n解释器能运行", 80, 310, "blue"),
               n("deps", "② 章节依赖\n所选环境能导入", 460, 310, "green"),
               n("request", "③ 请求草图\n本地合同成立", 840, 310, "violet"),
               n("provider", "④ 真实调用\n账户与网络验收", 1220, 310, "orange"),
               n("proof", "本附录的离线证据\n程序、输入、草图和错误夹具", 220, 610, "green", 620),
               n("notrun", "真实模型\n未运行就记 not_run", 1040, 610, "orange", 460)),
              (Edge("e1", "run", "deps"), Edge("e2", "deps", "request"),
               Edge("e3", "request", "provider", color="orange", dash="dashed")),
              "工具装得多，不等于工作台可用；每一步都有自己的验收对象。"),
        Scene("02-environment", "命令找谁，包就装给谁",
              "导入看解释器；相对路径看当前目录。两条线都需要对齐。",
              (n("shell", "终端\n命令查找", 80, 250, "blue"),
               n("python", "所选解释器\nsys.executable", 570, 250, "green", 390),
               n("packages", "该环境的依赖\npython -m pip", 1170, 250, "violet", 350),
               n("cwd", "当前工作目录\n仓库根目录", 80, 590, "blue"),
               n("entry", "程序入口\n模块路径与相对文件", 570, 590, "green", 390),
               n("wrong", "env-A 安装\nenv-B 运行仍会失败", 1170, 590, "orange", 350)),
              (Edge("e1", "shell", "python", "找到程序"), Edge("e2", "python", "packages", "决定可见包", "violet"),
               Edge("e3", "cwd", "entry", "路径从这里起算"), Edge("e4", "python", "entry", "运行", "green")),
              "虚拟环境隔离依赖，不隔离文件和网络；直接调用环境内解释器即可。"),
        Scene("03-api-contract", "SDK 名字，不是 Provider 身份",
              "五项配置共同决定请求；离线草图不会读取凭据，也不会跨过网络边界。",
              (n("provider", "Provider\n谁处理请求", 60, 190, "blue", 330, 100),
               n("key", "凭据\n服务端注入", 60, 340, "violet", 330, 100),
               n("url", "地址\nbase URL / 端点", 60, 490, "green", 330, 100),
               n("protocol", "协议\ninput / messages", 60, 640, "violet", 330, 100),
               n("model", "模型 ID\n账户可用标识", 560, 190, "orange", 350, 100),
               n("build", "本地请求构造\n不公开认证头", 560, 460, "blue", 350, 150),
               n("server", "Provider 接口\n需账户、网络与预算", 1160, 330, "orange", 360, 140),
               n("response", "实际响应\n新增远端证据", 1160, 630, "green", 360, 110)),
              (Edge("e1", "provider", "build"), Edge("e2", "key", "build", color="violet"),
               Edge("e3", "url", "build", color="green"), Edge("e4", "protocol", "build", color="violet"),
               Edge("e5", "model", "build", color="orange"),
               Edge("e6", "build", "server", "显式发送", "orange", "dashed"),
               Edge("e7", "server", "response", "接收", "green")),
              "接口外形兼容 ≠ 全部能力等价；小请求通过 ≠ 应用迁移完成。"),
        Scene("04-troubleshooting", "先定位失败层，再改变一个变量",
              "有 HTTP 响应，不等于模型已执行；超时，也不等于服务端什么都没做。",
              (n("error", "一条失败记录\n命令 + 类型 + 安全信息", 80, 410, "blue", 370),
               n("local", "尚未发送\n导入 / JSON / 文件", 600, 190, "green", 380),
               n("http", "收到 HTTP 响应\n状态码 + 原因码", 600, 410, "violet", 380),
               n("unknown", "无明确响应\n连接失败 / 超时", 600, 630, "orange", 380),
               n("fix", "修正本机输入\n解释器 / 路径 / 参数", 1180, 190, "green", 330),
               n("account", "分清永久与暂时\n查账户或有界重试", 1180, 410, "violet", 330),
               n("inspect", "保留 unknown\n核对尝试与副作用", 1180, 630, "orange", 330)),
              (Edge("e1", "error", "local"), Edge("e2", "error", "http", color="violet"),
               Edge("e3", "error", "unknown", color="orange"), Edge("e4", "local", "fix", color="green"),
               Edge("e5", "http", "account", color="violet"), Edge("e6", "unknown", "inspect", color="orange")),
              "429 先读原因码；未知原因先检查；不要用无限重试代替诊断。"),
    )


def render(scene):
    svg = _svg(scene)
    drawing = _tldraw(scene)
    # The shared renderer centers incoming edges. This API hub deliberately
    # fans its four left-side inputs out, in both the editable and print forms.
    if scene.stem == "03-api-contract":
        nodes = {node.identity: node for node in scene.nodes}
        records = {record["id"]: record for record in drawing["records"]}
        end = nodes["build"]
        for index, edge in enumerate(scene.edges[:4], 1):
            start = nodes[edge.start]
            sx, sy = _point(start, end)
            ex, ey = _point(end, start)
            old = f"M {sx:.1f} {sy:.1f} L {ex:.1f} {ey:.1f}"
            y = end.y + end.h * index / 5
            new = f"M {sx:.1f} {sy:.1f} L {end.x:.1f} {y:.1f}"
            if old not in svg:
                raise ValueError("shared SVG renderer changed its path contract")
            svg = svg.replace(old, new, 1)
            records["shape:" + edge.identity]["props"]["end"]["normalizedAnchor"] = {
                "x": 0, "y": index / 5}
    return svg, drawing


def generate(root: Path):
    outputs = []
    for scene in scenes():
        svg, drawing = render(scene)
        for folder, extension, content in (
            ("infographic/appendix_a", ".tldr", json.dumps(drawing, ensure_ascii=False, indent=2) + "\n"),
            ("book/images/appendix-a", ".svg", svg)):
            path = root / folder / (scene.stem + extension)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
            outputs.append(path)
    return tuple(outputs)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    for path in generate(root):
        print(path.relative_to(root).as_posix())
