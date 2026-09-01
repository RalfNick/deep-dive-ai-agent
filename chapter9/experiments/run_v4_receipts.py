from chapter9.experiments.version_output import print_version


def main() -> int:
    return print_version(4, "写工具授权与可信回执", "不覆盖跨进程事务与持久化幂等。")


if __name__ == "__main__":
    raise SystemExit(main())

