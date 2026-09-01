from chapter9.experiments.version_output import print_version


def main() -> int:
    return print_version(6, "现代与兼容模式 MCP Client", "不实现或伪造底层 JSON-RPC 传输。")


if __name__ == "__main__":
    raise SystemExit(main())

