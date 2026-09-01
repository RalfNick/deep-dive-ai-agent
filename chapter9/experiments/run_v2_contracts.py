from chapter9.experiments.version_output import print_version


def main() -> int:
    return print_version(2, "ToolDefinition、ToolCall 与 ToolResult", "不代表工具调用已经形成循环。")


if __name__ == "__main__":
    raise SystemExit(main())

