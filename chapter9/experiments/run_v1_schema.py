from chapter9.experiments.version_output import print_version


def main() -> int:
    return print_version(1, "JSON 提议与参数合同", "不代表完整实现了 JSON Schema。")


if __name__ == "__main__":
    raise SystemExit(main())

