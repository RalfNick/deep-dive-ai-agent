from chapter9.experiments.version_output import print_version


def main() -> int:
    return print_version(3, "固定三步决策策略", "不比较任何大模型的规划质量。")


if __name__ == "__main__":
    raise SystemExit(main())

