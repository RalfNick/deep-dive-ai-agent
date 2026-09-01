from chapter9.experiments.version_output import print_version


def main() -> int:
    return print_version(5, "官方 SDK 进程内 MCP Server", "不代表已部署远程生产服务。")


if __name__ == "__main__":
    raise SystemExit(main())

