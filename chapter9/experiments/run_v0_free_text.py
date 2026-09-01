from chapter9.experiments.version_output import print_version


def main() -> int:
    return print_version(0, "自由文本完成声明", "不代表真实模型的误报率。")


if __name__ == "__main__":
    raise SystemExit(main())

